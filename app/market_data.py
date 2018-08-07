#
# (c) 2018 elias/vanissoft
#
'''


'''

import pandas as pd
import numpy as np
import os
import pyarrow.parquet as pq

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
			if df is not None:
				df = pd.concat([df, df2])
			else:
				df = df2
		#df.reset_index(inplace=True)

		if cls.Dataframe2 is None:
			cls.Dataframe2 = df
		else:
			cls.Dataframe2 = pd.concat([cls.Dataframe2, df])
		print(len(cls.Dataframe2))

	@classmethod
	def _next_file(cls):
		if len(cls.File_list) == 0:
			return False
		file = cls.File_list.pop(0)
		df =  pq.read_table(file, nthreads=2).to_pandas()
		cls.Dataframe = df
		cls._extract()
		print("process", file)
		return True


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

			self.stats_by_pair = df.groupby('pair').agg({'pays_amount': 'sum', 'receives_amount': 'sum', 'price': 'mean', 'pair': 'count'}).sort_values('pair', ascending=False)
			self.stats_by_pair['pair_id'] = self.stats_by_pair.index
			self.stats_by_pair['pair_text'] = self.stats_by_pair['pair_id'].apply(lambda x: self.Assets_id[x.split(':')[0]] + "/" + self.Assets_id[x.split(':')[1]])

			self.stats_by_account = df.groupby('account_id').agg({'pair': 'count'}).sort_values('pair', ascending=False)
			self.stats_by_account['account_id'] = self.stats_by_account.index

			self.stats_by_account_pair = df.groupby(['account_id', 'pair']).agg({'pair': 'count'}).sort_values('pair', ascending=False)
			self.stats_by_account_pair['account_id'] = self.stats_by_account_pair.index.get_level_values(0)
			self.stats_by_account_pair['pair_id'] = self.stats_by_account_pair.index.get_level_values(1)
			self.stats_by_account_pair['pair_text'] = self.stats_by_account_pair['pair_id'].apply(lambda x: self.Assets_id[x.split(':')[0]] + "/" + self.Assets_id[x.split(':')[1]])

			Cache = (self.stats_by_token, self.stats_by_pair, self.stats_by_account, self.stats_by_account_pair)




if __name__ == "__main__":
	import os
	print("Starting")
	#d = Account_data([account, account2])
	#while d._next_file() is True:
	#	pass
	print('end')