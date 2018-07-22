#
# (c) 2017 elias/vanissoft
#
#
#
"""
	Data Proxy
"""




from config import *
import json
import arrow
import pickle
import pandas as pd
from os import path, remove


class MarketTrades():

	Data = {}
	is_saved = {}

	def __init__(self, mkt=None):
		self.market = mkt

	# th = Bitshares.rpc.get_trade_history(pairs[1], pairs[0], date_init, date_end, 100)
	def store(self, data):
		"""
		# {'date': '2017-11-27T03:49:30', 'amount': '0.01996100000000000', 'value': '1.00004000000000004', 'price': '50.09969440408797681'}
		:param market:
		:param data: {'date': '2017-11-27T03:49:30', 'amount': '0.01996100000000000', 'value': '1.00004000000000004', 'price': '50.09969440408797681'}
		:return:
		"""
		if self.market is None:
			return None
		data2 = []
		for d in data:
			amount = float(d['amount'])
			price = float(d['price'])
			if amount + price != float('Infinity'):
				data2.append({'date': d['date'], 'price': price, 'amount': amount})
		df = pd.DataFrame(data2)
		df['datetime'] = pd.to_datetime(df['date'])
		df.index = df['datetime']

		# from < to  old < new

		if self.market not in MarketTrades.Data:
			self._load()
		if self.market not in MarketTrades.Data:
			MarketTrades.Data[self.market] = df
		else:
			# append
			MarketTrades.Data[self.market] = MarketTrades.Data[self.market].append(df)
		Redisdb.set("status:market_last:" + self.market,
				MarketTrades.Data[self.market].index[-1].to_pydatetime().isoformat() + "|" +
				MarketTrades.Data[self.market].index[0].to_pydatetime().isoformat())
		MarketTrades.is_saved[self.market] = False


	# data loader: th = Bitshares.rpc.get_market_history(symb2, symb1, 3600, date_end, date_init, api_id=3)
	def store_old_markethistory(self, data, prec1, prec2):
		"""
		:param market:
		:param data: {'close_quote': 869686, 'quote_volume': 237773520, 'high_quote': 93771222, 'close_base': 31308,
						'open_quote': 134716056, 'high_base': 3375764, 'low_base': 31308,
						'key': {'open': '2017-12-01T13:00:00', 'base': '1.3.0', 'quote': '1.3.1564', 'seconds': 3600},
						'id': '5.1.4013368', 'base_volume': 8559846, 'open_base': 4849778, 'low_quote': 869686}
		:return:
		"""
		if self.market is None or len(data) == 0:
			return False
		if self.market == "BTC/USD":
			print()
		data2 = []
		for d in data[::-1]:
			lq = round(int(d['close_quote'])/10**prec1, prec1)
			lb = round(int(d['close_base'])/10**prec2, prec2)
			base_volume = round(int(d['base_volume'])/10**prec2, prec2)
			if lq == 0 or lb == 0 or base_volume < (1/(10**prec2))*10:
				#print(self.market, d['key']['open'], d['high_quote'], d['low_quote'], d['high_base'], d['low_base'])
				pass
			else:
				mid_price = round(lb/lq, prec2)
				if mid_price != float('Infinity'):
					data2.append({'date': d['key']['open'], 'price': mid_price, 'volume': base_volume})
		if len(data2) == 0:
			return False
		try:
			df = pd.DataFrame(data2)
			df['datetime'] = pd.to_datetime(df['date'])
		except Exception as err:
			print(err.__repr__())
		df.index = df['datetime']
		dfg = df.resample('60min').agg({'openbid': 'first', 'highbid': 'max', 'lowbid': 'min', 'closebid': 'last', 'volume': ['first','sum']}).bfill()

		if self.market not in MarketTrades.Data:
			self._load()
		if self.market not in MarketTrades.Data:
			MarketTrades.Data[self.market] = dfg
		else:
			# append
			MarketTrades.Data[self.market] = MarketTrades.Data[self.market].append(dfg)
		MarketTrades.is_saved[self.market] = False
		return True


	def get(self):
		if self.market not in MarketTrades.Data:
			self._load()
		if self.market not in MarketTrades.Data:
			return None
		else:
			return MarketTrades.Data[self.market]


	# TODO: don't save every time it updates
	def save(self, mkt=None):
		if mkt is None:
			mkt = self.market
		file = "market_data_" + mkt.replace("/", "_") + ".dat"
		with open(file, 'wb') as f:
			pickle.dump(MarketTrades.Data[mkt], f)
		MarketTrades.is_saved[mkt] = True


	def _load(self):
		file = "market_data_" + self.market.replace("/", "_") + ".dat"
		if path.isfile(file):
			try:
				with open(file, 'rb') as f:
					MarketTrades.Data[self.market] = pickle.load(f)
			except Exception as err:
				remove(file)
				Redisdb.delete("status:market:" + self.market)
				print(err.__repr__())
			# recalc init end dates
			df = MarketTrades.Data[self.market]
			MarketTrades.is_saved[self.market] = True


	def save_all(self):
		for mkt in MarketTrades.is_saved.items():
			if not mkt[1]:
				self.save(mkt[0])
