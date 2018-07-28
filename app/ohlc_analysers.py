#
# (c) 2018 elias/vanissoft
#
'''


'''

import os
import arrow
import matplotlib.pyplot as plt
plt.style.use('Solarize_Light2')
import numpy as np
import pandas as pd
import tulipy as ti

#TODO:

class Common:

	# TODO: allow to incremental adding of data
	def load_data(self):
		os.chdir('../data')
		from glob import glob
		files = glob('*.parquet')
		dfl = []
		for r in arrow.Arrow.range('month', self.range[0], self.range[1].ceil('month')):
			if r.year < 2017:
				if r.month == 1:
					f = 'bts_trades_{:04d}.parquet'.format(r.year)
				else:
					continue
			else:
				f = 'bts_trades_{:04d}{:02d}.parquet'.format(r.year, r.month)
			d = pd.read_parquet(f, 'pyarrow')
			dfl.append(d)
		self.dfo = pd.concat(dfl)

	def __init__(self, dataframe=None, range=None):
		self.range=[]
		if dataframe is None:
			if range is None:
				self.range = (arrow.utcnow().shift(days=30), arrow.utcnow())
			else:
				self.range = [range[0], range[1].ceil('day')]
			self.load_data()
		else:
			self.dfo = dataframe
		self.dfo = self.dfo.loc[(self.dfo.block_time > self.range[0].datetime.replace(tzinfo=None))&(self.dfo.block_time < self.range[1].datetime.replace(tzinfo=None))]
		self.dfo.set_index('block_time', drop=False, inplace=True)
		self.dff = None
		self.df_ohlc = None


	def filter(self, pair='1.3.0:1.3.113', dust=[1,1]):
		dff = self.dfo.loc[self.dfo.pair == pair]
		#dff = dff.loc[(dff.quote_amount>dust[0]) & (dff.base_amount>dust[1])]
		dff['volume'] = dff['quote_amount']
		# duplicate with the inverse market
		tmp = pair.split(':')
		pair_inv = tmp[1]+':'+tmp[0]
		dff2 = self.dfo.loc[self.dfo.pair == pair_inv]
		dff2['price'] = dff2['quote_amount'] / dff2['base_amount']
		dff2['volume'] = dff2['base_amount']
		self.dff = pd.concat((dff, dff2))
		print(self.dff.count())
		return self

	def ohlc(self, timelapse='1h', fill=True):
		if fill:
			self.df_ohlc = self.dff.resample(timelapse, how={'price': 'ohlc', 'base_amount': 'sum'}).ffill()
		else:
			self.df_ohlc = self.dff.resample(timelapse, how={'price': 'ohlc', 'base_amount': 'sum'})
		self.df_ohlc = self.df_ohlc.dropna()
		self.df_ohlc['time'] = self.df_ohlc.index
		return self


	def _add_column_to_ohlc(self, name='tulip', data=None):
		if type(data) == type(tuple()):
			ret = []
			for t in data:
				ret.append(t.tolist())
		else:
			ret = [data.tolist()]
		sufix = 0
		for r in ret:
			pad = list((np.nan,) * (self.df_ohlc.__len__() - len(r)))
			pad.extend(r)
			if sufix > 0:
				sname = name + '_' + str(sufix)
			else:
				sname = name

			ser = pd.Series(pad, name=sname)
			ser.index = self.df_ohlc.index
			self.df_ohlc[sname] = ser
			sufix += 1


# utils
def _zero_padding(arr, length):
	return np.concatenate((np.zeros(length-len(arr)), arr))

def numpy_ewma_vectorized_v2(data, window):
	"""
	www.quantopian.com/posts/wavetrend-based-algorithm-results
	"""

	alpha = 2 /(window + 1.0)
	alpha_rev = 1-alpha
	n = data.shape[0]

	pows = alpha_rev**(np.arange(n+1))

	scale_arr = 1/pows[:-1]
	offset = data[0]*pows[1:]
	pw0 = alpha*alpha_rev**(n-1)

	mult = data*pw0*scale_arr
	cumsums = mult.cumsum()
	out = offset + cumsums*scale_arr[::-1]
	return out


class Analyze(Common):

	def sma(self, name='sma', period=5):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.sma(self.df_ohlc.price.close.values, period=period))

	def ema(self, name='ema', period=5):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.ema(self.df_ohlc.price.close.values, period=period))

	def stoch(self, name='stoch', kp=14, ksp=3, d=3):
		if len(self.df_ohlc) > kp:
			self._add_column_to_ohlc(name, ti.stoch(self.df_ohlc.price.high.values, self.df_ohlc.price.low.values, self.df_ohlc.price.close.values, kp, ksp, d))

	def stoch_rsi(self, name='stoch_rsi', kp=14, ksp=3, d=3):
		if len(self.df_ohlc) > kp:
			if 'rsi' not in self.df_ohlc.columns:
				self._add_column_to_ohlc("rsi", ti.rsi(self.df_ohlc.price.close.values, kp))
			v = self.df_ohlc.rsi.dropna().values
			self._add_column_to_ohlc(name, ti.stoch(v, v, v, kp, ksp, d))

	def cci(self, name='cci', period=20):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.cci(self.df_ohlc.price.high.values, self.df_ohlc.price.low.values, self.df_ohlc.price.close.values, period))

	def rsi(self, name='rsi', period=14):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.rsi(self.df_ohlc.price.close.values, period))

	def wavetrend(self, name='wt', d_factor=0.035):
		"""
		https://www.quantopian.com/posts/wavetrend-oscillator
		"""
		ap = (self.df_ohlc.price.high + self.df_ohlc.price.low + self.df_ohlc.price.close)/3
		ap = ap.values
		#esa = numpy_ewma_vectorized_v2(ap, 10)
		esa = ti.ema(ap,10)
		diff_ = abs(ap - esa)
		d = ti.ema(diff_, 10)
		d[0] = d[1]
		ci = (ap - esa) / (d_factor * d)
		tci = ti.ema(ci, 21)
		wt1 = _zero_padding(tci, len(ap))
		self._add_column_to_ohlc(name, wt1)


def test_stoch_rsi():
	a = Analyze(range=(arrow.get('2018-07-05'), arrow.get('2018-07-06')))
	a.filter()
	ts = ['5min', '8min', '13min', '21min', '34min']
	series = []
	for tl in ts:
		a.ohlc(timelapse=tl).stoch_rsi()
		s = a.df_ohlc.stoch_rsi
		s.name = s.name+"_"+tl
		series.append(s)
	series.append(a.df_ohlc.price.open)
	series.append(a.df_ohlc.price.close)
	df = pd.concat(series, axis=1)
	for col in df.columns:
		df[col] = df[col].interpolate(method='linear')
	df['time'] = df.index
	g = ['stoch_rsi_{}'.format(x) for x in ts]
	df[g].plot()
	print()


def test_prophet():
	from fbprophet import Prophet
	a = Analyze(range=(arrow.get('2016-01-01'), arrow.get('2018-07-15')))
	a.filter()
	df = a.ohlc(timelapse="8h").df_ohlc
	df['ds'] = df.index
	df['y'] = df.price.close
	m = Prophet(weekly_seasonality=True)
	m.add_seasonality(name='8h', period=8, fourier_order=5)
	m.add_seasonality(name='12h', period=12, fourier_order=5)
	m.add_seasonality(name='1w', period=24*7, fourier_order=5)
	m = m.fit(df)
	future = m.make_future_dataframe(periods=360, freq='D')
	fcst = m.predict(future)
	#m.plot(fcst).savefig("froga3.svg", format='svg')
	m.plot(fcst).savefig("froga6.png", format='png')
	print()




if __name__ == "__main__":
	import os
	os.chdir('../data')
	print("Starting")
	print("ok1")
	test_prophet()

	if False:
		d = []
		for i in (21,34,55,89,144,233):
			a.sma('sma_'+str(i), i)
			d.append('sma_'+str(i))
	#a.df_ohlc[d].plot()
	#a.df_ohlc[('price', 'close')].plot()

	print('end')