#
# (c) 2018 elias/vanissoft
#
'''


'''

import pandas as pd
import numpy as np
import os
import json
import pickle
import pyarrow.parquet as pq
import arrow
from config import *




class MarketDataFeeder:
	"""
	Read static historic data and calls consumers.
	Refreshes with new data.
	Raw data for Account filtered movs.
	Timeframe data for token/pair filtered.

	Consumer samples:
		* BTS/USD, USD/CNY price with 1day timeframe
		* account trades
		* last 24h statistics
	"""
	Requests_account = {}
	Requests_token = {}
	Requests_pair = {}
	Parquet_files = []
	Files_to_process = []
	Df_raw_current = None
	Current_file = None
	Last_file = None
	Last_file_date = None
	Current_range = None
	Datastores_account = {}
	Datastores_token = {}
	Datastores_pair = {}
	Date_ranges = []


	@classmethod
	def update(cls):
		pass

	def __init__(self):
		cls = self.__class__
		if len(cls.Parquet_files) == 0:
			os.chdir('../data')
			from glob import glob
			cls.Parquet_files = glob('bts_trades_*.parquet')
			cls.Parquet_files.sort(reverse=True)


	@classmethod
	def precharge_df(cls):
		for req in cls.Requests_account.items():
			for acc in req[1]['accounts']:
				if cls.Datastores_account[acc]['precharged']:
					continue
				df_file = 'datastores_account_{}'.format(acc)
				rtn = Redisdb.get(df_file)
				if rtn is not None:
					cls.Datastores_account[acc]['files'] = json.loads(rtn.decode('utf8'))['files']
				if os.path.isfile(df_file):
					df = pd.read_parquet(df_file, 'pyarrow')
					cls.Datastores_account[acc]['df'] = df
					cls.Datastores_account[acc]['range'] = [arrow.get(df.block_time.min()), arrow.get(df.block_time.max())]
					cls.Datastores_account[acc]['precharged'] = True
		print('precharge')

	@classmethod
	def _files_range(cls, range, excl_list=[]):
		"""
		setup the files to read
		:return:
		"""
		tp = []
		for f in cls.Parquet_files:
			f0 = f.split('.')[0]
			if f0[11:15] < '2018':
				f0 = f0.split('.')[0]+"99"
			f1 = "bts_trades_" + range[0].isoformat().replace('-', '')[:8]
			f2 = "bts_trades_" + range[1].isoformat().replace('-', '')[:8]
			if f0 >= f1 and f0 <= f2:
				if f not in cls.Files_to_process and f not in excl_list:
					cls.Files_to_process.append(f)

	@classmethod
	def step(cls):
		if len(cls.Files_to_process) > 0:
			cls.readfile(cls.Files_to_process.pop(0))
			Redisdb.rpush('operations_bg', json.dumps({'call': 'marketdatafeeder_step', 'module': 'general'}))
			return True
		return False

	@classmethod
	def request(cls, data):
		"""
		data.keys = name, type, callback, daterange, pair=None, token=None
		:return: pandas.DataFrame
		"""
		reqr = data['daterange']
		if reqr[0] is None:
			reqr[0] = arrow.utcnow().shift(years=-10)
		if reqr[1] is None:
			reqr[1] = arrow.utcnow().shift(years=+10)

		excl_list = []
		if data['type'] == 'account_trades':
			cls.Requests_account[data['name']] = data
			for acc in data['accounts']:
				if acc not in cls.Datastores_account:
					cls.Datastores_account[acc] = {'df': None, 'files': [], 'range': [None, None], 'df_file': None, 'precharged': False}

		elif data['type'] == 'token':
			cls.Requests_token[data['name']] = data

		elif data['type'] == 'pair':
			cls.Requests_pair[data['name']] = data

		cls.precharge_df()

		# exclusion list
		if data['type'] == 'account_trades':
			for acc in data['accounts']:
				for f in cls.Datastores_account[acc]['files']:
					if f not in excl_list:
						excl_list.append(f)

		elif data['type'] == 'token':
			pass
		elif data['type'] == 'pair':
			pass

		cls._reqlastdata()  # refresh more recent data
		cls._files_range(reqr, excl_list)


	@classmethod
	def _consolidate(cls):
		"""
		Fills the Datastores with cls.Df_raw_current data and serve requests.

		:return:
		"""
		for req in cls.Requests_account.items():
			df = cls.Df_raw_current
			for acc in req[1]['accounts']:
				if cls.Last_file != cls.Current_file and cls.Current_file in cls.Datastores_account[acc]['files']:
					continue
				else:
					cls.Datastores_account[acc]['files'].append(cls.Current_file)
				df2 = df.loc[(df.account_id == acc)]
				if len(df2) == 0:
					continue
				if cls.Datastores_account[acc]['df'] is not None and len(cls.Datastores_account[acc]) > 0:
					df3 = pd.concat([cls.Datastores_account[acc]['df'], df2])
					df3 = df3.drop_duplicates()
				else:
					df3 = df2
				cls.Datastores_account[acc]['df'] = df3
				cls.Datastores_account[acc]['range'] = [arrow.get(df3.block_time.min()), arrow.get(df3.block_time.max())]
				print("len Datastores_account", len(df3))
		cls.resprequesters()

	@classmethod
	def resprequesters(cls):
		for req in cls.Requests_account.items():
			for acc in req[1]['accounts']:
				if cls.Datastores_account[acc]['range'][0] is None:
					dts_range = [arrow.get('20000101'), arrow.get('20000101')]
				else:
					dts_range = cls.Datastores_account[acc]['range']
				if (len(cls.Files_to_process) == 0) or \
					(len(cls.Parquet_files) == len(cls.Datastores_account[acc])) or \
					(dts_range[0] <= req[1]['daterange'][0] and dts_range[1] >= req[1]['daterange'][1]):
					if cls.Datastores_account[acc]['df'] is not None:
						req[1]['callback'](cls.Datastores_account[acc]['df'])
						#persistence
						df_file = 'datastores_account_{}'.format(acc)
						cls.Datastores_account[acc]['df'].to_parquet(df_file, 'fastparquet', 'GZIP')
						Redisdb.set(df_file, json.dumps({'files': cls.Datastores_account[acc]['files']}))

	@classmethod
	def readfile(cls, file):
		if os.path.isfile(file):
			print("reading", file)
			df = pd.read_parquet(file, 'pyarrow')
			cls.Current_file = file
			cls.Current_range = [arrow.get(df.block_time.min()), arrow.get(df.block_time.max())]
			cls.Df_raw_current = df
			cls._consolidate()
		else:
			return None


	@classmethod
	def _reqlastdata(cls):
		fnow = arrow.utcnow().isoformat().replace('-', '')[:8]
		cls.Last_file = 'bts_trades_' + fnow + '.parquet'
		if cls.Last_file_date is None:
			isnew = True
		elif cls.Last_file_date <= arrow.get(os.stat(cls.Last_file).st_mtime):
			isnew = True
		else:
			isnew = False
		if isnew:
			cls.Last_file_date = arrow.get(os.stat(cls.Last_file).st_mtime)
			if cls.Last_file not in cls.Files_to_process:
				cls.Files_to_process.insert(0, cls.Last_file)



class Account_data:
	"""
	Trades done by accounts.
	Reads historic data harvested by tradehistory.py

	Example:
	To obtain all trades from accounts:
		d = Account_data(['account1', 'account2', ...])
		num = 0
		while d._next_file() is True:
			num += 1
			if num % 5 == 0:
				d._save()

	"""
	Dataframe = None
	Accounts_id = {}
	Accounts_name = {}
	File_list = []
	MarketDataFeeder = None
	CntToSave = 0


	@classmethod
	def data_received(cls, df):
		print("data received")
		print(df.block_time.min(), df.block_time.max())
		if cls.Callback is not None:
			cls.Callback(df)


	@classmethod
	def _save(cls):
		cls.Dataframe.to_parquet('bts_account_movs.parquet', 'fastparquet', 'GZIP')

	def __init__(self, accounts, MDF, callback):
		cls = self.__class__
		from bitshares.account import Account
		for acc in accounts:
			id = Account(acc).identifier
			cls.Accounts_id[id] = acc
			cls.Accounts_name[acc] = id
		cls.Dataframe = None
		cls.Callback = callback
		# last data
		last = 'bts_account_movs.parquet'
		cls.DateRange = [arrow.utcnow(), arrow.utcnow()]
		dr = [arrow.utcnow().shift(years=-10), arrow.utcnow().shift(years=10)]
		if os.path.isfile(last):
			df = pd.read_parquet(last, 'pyarrow')
			for acc in accounts:
				df2 = df.loc[(df.account_id == cls.Accounts_name[acc])]
				if len(df2) == 0:
					dr[0] = arrow.utcnow().shift(years=-10)
				else:
					dr[0] = min(dr[0], arrow.get(df.block_time.min()))
			dr[1] = arrow.utcnow()
			cls.DateRange = dr
			cls.Dataframe = df
			print('daterange', dr)

		dr[0] = arrow.utcnow().shift(days=-5)
		dr[1] = arrow.utcnow()
		MDF.request({'name': 'account', 'type': 'account_trades', 'callback': cls.data_received,
									  'accounts': cls.Accounts_id.keys(), 'daterange': dr})
		print("request account_trades", dr)




class Stats:
	#TODO: mechanism for invalidate cache
	Cache = None

	def _load_last_data(self):
		os.chdir('../data')
		from glob import glob
		files = glob('bts_trades_*.parquet')
		files.sort()
		#self.df = pd.read_parquet(files[-1], 'pyarrow')
		self.df = pq.read_table(files[-1], nthreads=4).to_pandas()
		import pickle
		with open('assets.pickle', 'rb') as h:
			tmp = pickle.load(h)
		self.Assets_id = {k: v for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}
		self.Assets_name = {v: k for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}

	def __init__(self):
		cls = self.__class__
		self.last = None
		self.df = None
		self.Assets_id = None
		self.Assets_name = None
		self.stats_by_token = None
		self.stats_by_pair = None
		self.stats_by_account = None
		self.stats_by_account_pair = None

		if cls.Cache is not None:
			self.stats_by_token, self.stats_by_pair, self.stats_by_account, self.stats_by_account_pair = cls.Cache
			return None
		self._load_last_data()

		df = self.df
		tmp = df.block_time.max() - df.block_time.min()
		self.data_days = ((tmp.components.days*24) + tmp.components.hours)/24
		d1 = df.groupby('pays_asset').agg({'pays_asset': 'count', 'pays_amount': 'sum'})
		d2 = df.groupby('receives_asset').agg({'receives_asset': 'count', 'receives_amount': 'sum'})
		d1['asset'] = d1.index
		d2['asset'] = d2.index
		d3 = pd.concat([d1, d2], axis=1)
		d3 = d3.fillna(0)
		d3['ops'] = d3.pays_asset + d3.receives_asset
		d3['volume'] = d3.pays_amount + d3.receives_amount
		d3.sort_values('ops', ascending=False, inplace=True)
		d3['ops_day'] = d3['ops'] / self.data_days
		d3['volume_day'] = d3['volume'] / self.data_days
		d3['asset_name'] = d3.index
		d3.replace({'asset_name': self.Assets_id}, inplace=True)

		self.stats_by_token = d3

		d1 = df.groupby('pair').agg({'pays_amount': 'sum', 'receives_amount': 'sum', 'price': 'mean', 'pair': 'count'}).sort_values('pair', ascending=False)
		d1['pair_id'] = d1.index
		d1['pair_text'] = d1['pair_id'].apply(lambda x: self.Assets_id[x.split(':')[0]] + "/" + self.Assets_id[x.split(':')[1]])

		rtn = Redisdb.get("settings_prefs_bases")
		if rtn is None:
			prefs = []
		else:
			prefs = json.loads(rtn.decode('utf8'))
		pairs = d1.pair_text.tolist()

		d1['invert'] = d1.pair_text.apply(lambda x: 1 if (prefs.index(x.split('/')[0]) if x.split('/')[0] in prefs else 999) < (prefs.index(x.split('/')[1]) if x.split('/')[1] in prefs else 998) else 0)

		d2 = d1.loc[(d1.invert==1)]
		d2[['pays_amount', 'receives_amount']] = d2[['receives_amount', 'pays_amount']]
		d2[['price']] = 1/d2[['price']]
		d2.pair_id = d2.pair_id.apply(lambda x: x.split(':')[1]+":"+x.split(':')[0])
		d2.pair_text = d2.pair_text.apply(lambda x: x.split('/')[1]+"/"+x.split('/')[0])
		d2.index = d2.pair_id

		d3 = pd.concat([d2, d1.loc[(d1.invert==0)]])

		d1 = d3.groupby('pair_id').agg({'pays_amount': 'sum', 'receives_amount': 'sum', 'price': 'mean', 'pair': 'sum'}).sort_values('pair', ascending=False)
		d1['pair_id'] = d1.index
		d1['pair_text'] = d1['pair_id'].apply(lambda x: self.Assets_id[x.split(':')[0]] + "/" + self.Assets_id[x.split(':')[1]])
		self.stats_by_pair = d1


		self.stats_by_account = df.groupby('account_id').agg({'pair': 'count'}).sort_values('pair', ascending=False)
		self.stats_by_account['account_id'] = self.stats_by_account.index

		self.stats_by_account_pair = df.groupby(['account_id', 'pair']).agg({'pair': 'count'}).sort_values('pair', ascending=False)
		self.stats_by_account_pair['account_id'] = self.stats_by_account_pair.index.get_level_values(0)
		self.stats_by_account_pair['pair_id'] = self.stats_by_account_pair.index.get_level_values(1)
		self.stats_by_account_pair['pair_text'] = self.stats_by_account_pair['pair_id'].apply(lambda x: self.Assets_id[x.split(':')[0]] + "/" + self.Assets_id[x.split(':')[1]])

		cls.Cache = (self.stats_by_token, self.stats_by_pair, self.stats_by_account, self.stats_by_account_pair)




if __name__ == "__main__":
	import os
	#stats = Stats()
	a=MarketDataFeeder()
	print("Starting")
	d = Account_data(['cjh.ant', 'gauto01'])
	while a.step():
		pass
	print('end')