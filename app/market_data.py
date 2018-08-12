#
# (c) 2018 elias/vanissoft
#
'''


'''

import pandas as pd
import numpy as np
import os
import json
import pyarrow.parquet as pq
import arrow
from config import *

Cache = None

class Account_data:
	Dataframe = None
	Dataframe2 = None
	Accounts_id = {}
	Accounts_name = {}
	File_list = []
	Assets_id = {}
	Assets_name = {}

	@classmethod
	def _extract(cls):
		df = None
		for acc in cls.Accounts_id.keys():
			df2 = cls.Dataframe.loc[(cls.Dataframe.account_id == acc)]
			if len(df2) == 0:
				continue
			if df is not None and len(df2)>0:
				df = pd.concat([df, df2])
			else:
				df = df2
		if df is None:
			return
		#df.reset_index(inplace=True)
		print(df.block_time.min())
		if cls.Dataframe2 is None:
			cls.Dataframe2 = df
		else:
			df = pd.concat([cls.Dataframe2, df])
			cls.Dataframe2 = df.drop_duplicates()
		print(len(cls.Dataframe2))

	@classmethod
	def _next_file(cls):
		dr = [cls.DateRange[n].isoformat().replace('-','')[:8] for n in range(0,2)]
		while True:
			if len(cls.File_list) == 0:
				return False
			file = cls.File_list.pop(0)
			dt = file.split('_')[2].split('.')[0]
			if dt >= dr[1]:
				break
			if dt < dr[0]:
				break
			print("drop", file)
		cls.Dataframe = pd.read_parquet(file)
		cls._extract()
		print("process", file)
		return True

	@classmethod
	def _save(cls):
		cls.Dataframe2.to_parquet('bts_account_movs.parquet', 'fastparquet', 'GZIP')

	def __init__(self, accounts):
		from bitshares.account import Account
		cls = self.__class__
		for acc in accounts:
			id = Account(acc).identifier
			cls.Accounts_id[id] = acc
			cls.Accounts_name[acc] = id
		cls.Dataframe = None
		os.chdir('../data')
		from glob import glob
		cls.File_list = glob('*.parquet')
		cls.File_list.sort(reverse=True)
		import pickle
		with open('assets.pickle', 'rb') as h:
			tmp = pickle.load(h)
		cls.Assets_id = {k: v for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}
		cls.Assets_name = {v: k for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}
		# last data
		last = 'bts_account_movs.parquet'
		cls.DateRange = [arrow.utcnow(), arrow.utcnow()]
		if len(glob(last)) > 0:
			df = pd.read_parquet(last)
			dr = [arrow.utcnow().shift(years=-10), arrow.utcnow().shift(years=10)]
			for acc in accounts:
				df2 = df.loc[(df.account_id == cls.Accounts_name[acc])]
				if len(df2) == 0:
					dr[0] = max(dr[0], arrow.utcnow())
					dr[1] = min(dr[1], arrow.utcnow())
				else:
					dr[0] = max(dr[0], arrow.get(df.block_time.min()))
					dr[1] = min(dr[1], arrow.get(df.block_time.max()))
			cls.DateRange = dr
			cls.Dataframe2 = df
			print('daterange', dr)



class Stats:
	#TODO: mechanism for invalidate cache

	def _load_last_data(self):
		os.chdir('../data')
		from glob import glob
		files = glob('*.parquet')
		files.sort()
		#self.df = pd.read_parquet(files[-1], 'pyarrow')
		self.df = pq.read_table(files[-1], nthreads=4).to_pandas()
		import pickle
		with open('assets.pickle', 'rb') as h:
			tmp = pickle.load(h)
		self.Assets_id = {k: v for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}
		self.Assets_name = {v: k for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}

	def __init__(self):
		global Cache
		self.last = None
		self.df = None
		self.Assets_id = None
		self.Assets_name = None
		self.stats_by_token = None
		self.stats_by_pair = None
		self.stats_by_account = None
		self.stats_by_account_pair = None

		if Cache is not None:
			self.stats_by_token, self.stats_by_pair, self.stats_by_account, self.stats_by_account_pair = Cache
		else:
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

			Cache = (self.stats_by_token, self.stats_by_pair, self.stats_by_account, self.stats_by_account_pair)




if __name__ == "__main__":
	import os
	#stats = Stats()
	print("Starting")
	d = Account_data(['tximiss0', 'eliserio0'])
	num = 0
	while d._next_file() is True:
		num += 1
		if num > 5:
			num = 0
			d._save()
	print('end')