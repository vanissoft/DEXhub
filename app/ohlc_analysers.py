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
import json
from market_data import Pair_data, MarketDataFeeder
from config import *


class Common:

	MDF = None

	def data_received(self, pair, df):
		print('data')
		self.dfo = df
		self.callback(self, pair, df)

	#TODO: local steps are temporal
	def load_data(self):
		cls = self.__class__
		b = Pair_data(self.pairs, '5min', 2, cls.MDF, self.data_received)
		while cls.MDF.step():
			pass

	def __init__(self, dataframe=None, range=None, minframe='5min', pairs=[], MDF=None, callback=None):
		cls = self.__class__
		self.range = []
		self.pairs = pairs
		self.callback = callback
		cls.MDF = MDF
		if dataframe is None:
			if range is None:
				self.range = [arrow.utcnow().shift(days=-10), arrow.utcnow()]
			elif range[0] is None:
				self.range = [arrow.utcnow().shift(days=-10), range[1].ceil('day')]
			elif range[1] is None:
				self.range = [range[0], arrow.utcnow().shift(days=1)]
			else:
				self.range = range
			self.load_data()
		else:
			self.dfo = dataframe
			#TODO: convert index to datetime
		#self.dfo = self.dfo.loc[(self.dfo.block_time > self.range[0].datetime.replace(tzinfo=None))&(self.dfo.block_time < self.range[1].datetime.replace(tzinfo=None))]
		#self.dfo.set_index('block_time', drop=False, inplace=True)
		self.df_ohlc = None


	def ohlc(self, timelapse='1h', fill=True):
		if fill:
			self.df_ohlc = self.dfo.resample(timelapse, how={'priceopen': 'first', 'pricehigh': 'max', 'pricelow':'min', 'priceclose':'last', 'amount_base': 'sum'}).ffill()
		else:
			self.df_ohlc = self.dfo.resample(timelapse, how={'priceopen': 'first', 'pricehigh': 'max', 'pricelow':'min', 'priceclose':'last', 'amount_base': 'sum'})
		# rename columns in multi-index
		#self.df_ohlc.columns = self.df_ohlc.columns.map(lambda x: x[0])
		#self.df_ohlc = self.df_ohlc.iloc[:, [0,4]]
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
			self._add_column_to_ohlc(name, ti.sma(self.df_ohlc.priceclose.values, period=period))

	def ema(self, name='ema', period=5):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.ema(self.df_ohlc.priceclose.values, period=period))

	def stoch(self, name='stoch', kp=14, ksp=3, d=3):
		if len(self.df_ohlc) > kp:
			self._add_column_to_ohlc(name, ti.stoch(self.df_ohlc.pricehigh.values, self.df_ohlc.pricelow.values, self.df_ohlc.priceclose.values, kp, ksp, d))

	def stoch_rsi(self, name='stoch_rsi', kp=14, ksp=3, d=3):
		if len(self.df_ohlc) > kp:
			if 'rsi' not in self.df_ohlc.columns:
				self._add_column_to_ohlc("rsi", ti.rsi(self.df_ohlc.priceclose.values, kp))
			v = self.df_ohlc.rsi.dropna().values
			self._add_column_to_ohlc(name, ti.stoch(v, v, v, kp, ksp, d))

	def cci(self, name='cci', period=20):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.cci(self.df_ohlc.pricehigh.values, self.df_ohlc.pricelow.values, self.df_ohlc.priceclose.values, period))

	def rsi(self, name='rsi', period=14):
		if len(self.df_ohlc) > period:
			self._add_column_to_ohlc(name, ti.rsi(self.df_ohlc.priceclose.values, period))

	def wavetrend(self, name='wt', d_factor=0.015):
		"""
		https://www.quantopian.com/posts/wavetrend-oscillator
		"""
		ap = (self.df_ohlc.pricehigh + self.df_ohlc.pricelow + self.df_ohlc.priceclose)/3
		ap = ap.values
		#esa = numpy_ewma_vectorized_v2(ap, 10)
		esa = ti.ema(ap, 10)
		d = ti.ema(abs(ap - esa), 10)
		# checking for zeroes
		i = 0
		while d[i] == 0:
			i += 1
		if i > 0:
			ap = ap[i:]
			esa = esa[i:]
			d = d[i:]
		ci = (ap - esa) / (d_factor * d)
		tci = ti.ema(ci, 21)
		wt1 = _zero_padding(tci, len(ap))
		self._add_column_to_ohlc(name, wt1)


def last_trades(module, range, pairs, MDF):

	def response(obj, pair, data):
		if 'dfo' not in obj.__dict__:
			return
		obj.ohlc(timelapse="1h", fill=False)
		rdates = obj.df_ohlc['time'].dt.to_pydatetime().tolist()
		rdates = [x.isoformat() for x in rdates]
		movs = [x for x in zip(rdates,
							   obj.df_ohlc.priceopen.tolist(), obj.df_ohlc.priceclose.tolist(),
							   obj.df_ohlc.pricelow.tolist(), obj.df_ohlc.pricehigh.tolist(),
							   obj.df_ohlc.amount_base.tolist())]
		Redisdb.rpush("datafeed", json.dumps({'module': module, 'market_trades': {'market': pair, 'data': movs}}))

	Analyze(range=(arrow.utcnow().shift(days=-7), arrow.utcnow()), pairs=pairs, MDF=MDF, callback=response)


def feed_wavetrend(module, range, pairs, MDF):

	def response2(obj, pair, data):
		ts = ['5min', '30min', '1h', '4h']
		series = []
		for tl in ts:
			obj.ohlc(timelapse=tl).wavetrend()
			s = obj.df_ohlc.wt.apply(lambda x: round(x, 0))
			s.name = s.name + "_" + tl
			series.append(s)
		series.append(obj.df_ohlc.priceclose)
		df = pd.concat(series, axis=1)
		for col in df.columns:
			df[col] = df[col].interpolate(method='linear')
		df['time'] = df.index
		g = ['wt_{}'.format(x) for x in ts]
		#df[-120:][g].plot()
		rdates = obj.df_ohlc['time'].dt.to_pydatetime().tolist()
		rdates = [x.isoformat() for x in rdates]
		movs = [x for x in zip(rdates, *[df['wt_'+x].tolist() for x in ts])]
		Redisdb.rpush("datafeed", json.dumps({'module': module,
											  'analysis_wavetrend':
												  {'market': pair, 'timelapse': ts, 'data': movs}}).replace("NaN", "null"))


	Analyze(range=[arrow.get('2018-08-03'), arrow.utcnow()], pairs=pairs, MDF=MarketDataFeeder(), callback=response2)



def test_stoch_rsi():
	print("Starting")
	def froga(data):
		print("response")

	a = Analyze(range=(arrow.get('2018-08-03'), arrow.get('2018-08-26')), pairs=['BTS/CNY'], MDF=MarketDataFeeder(), callback=froga)
	ts = ['5min', '30min', '1h', '4h'][:-1]
	series = []
	for tl in ts:
		a.ohlc(timelapse=tl).stoch_rsi()
		s = a.df_ohlc.stoch_rsi
		s.name = s.name+"_"+tl
		series.append(s)
	#series.append(a.df_ohlc.priceopen)
	series.append(a.df_ohlc.priceclose)
	df = pd.concat(series, axis=1)
	for col in df.columns:
		df[col] = df[col].interpolate(method='linear')
	df['time'] = df.index
	g = ['stoch_rsi_{}'.format(x) for x in ts]
	#df['priceclose'].plot()
	df[-20:][g].plot()

	a.ohlc(timelapse='1h').wavetrend()
	a.df_ohlc[['wt']].plot()

	print()


def test_wavetrend():
	print("Starting")

	def results(obj, pair, data):
		ts = ['5min', '30min', '1h', '4h']
		series = []
		for tl in ts:
			obj.ohlc(timelapse=tl).wavetrend()
			s = obj.df_ohlc.wt
			s.name = s.name + "_" + tl
			series.append(s)
		series.append(obj.df_ohlc.priceclose)
		df = pd.concat(series, axis=1)
		for col in df.columns:
			df[col] = df[col].interpolate(method='linear')
		df['time'] = df.index
		g = ['wt_{}'.format(x) for x in ts]
		df[-120:][g].plot()

	a = Analyze(range=[arrow.get('2018-08-03'), arrow.utcnow()], pairs=['BTS/CNY', 'OPEN.BTC/USD'], MDF=MarketDataFeeder(), callback=results)

	print()


def test_prophet():
	from fbprophet import Prophet
	a = Analyze(range=(arrow.get('2018-07-01'), arrow.get('2018-08-15')))
	df = a.ohlc(timelapse="1h").df_ohlc
	df['ds'] = df.index
	df['y'] = df.priceclose
	m = Prophet(weekly_seasonality=True)
	m.add_seasonality(name='8h', period=8, fourier_order=5)
	m.add_seasonality(name='12h', period=12, fourier_order=5)
	m.add_seasonality(name='1w', period=24*7, fourier_order=5)
	m = m.fit(df)
	future = m.make_future_dataframe(periods=30, freq='D')
	fcst = m.predict(future)
	#m.plot(fcst).savefig("froga3.svg", format='svg')
	m.plot(fcst).savefig("froga6.png", format='png')
	print()




if __name__ == "__main__":
	import os
	os.chdir('../data')
	print("Starting")
	print("ok1")
	#test_prophet()
	feed_wavetrend()
	if False:
		d = []
		for i in (21,34,55,89,144,233):
			a.sma('sma_'+str(i), i)
			d.append('sma_'+str(i))
	#a.df_ohlc[d].plot()
	#a.df_ohlc[('price', 'close')].plot()

	print('end')