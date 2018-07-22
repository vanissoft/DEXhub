#
# (c) 2018 elias/vanissoft
#
'''


'''

import pandas as pd
import os

Cache = None

class Stats:

	def _load_last_data(self):
		os.chdir('/tank/lana/bitshares/dex_hub_ev1/data')
		from glob import glob
		files = glob('*.parquet')
		files.sort()
		self.df = pd.read_parquet(files[-1], 'pyarrow')
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
			self.data_days = tmp.days
			d1 = df.groupby('quote_asset').agg({'quote_asset': 'count', 'quote_amount': 'sum'})
			d2 = df.groupby('base_asset').agg({'base_asset': 'count', 'base_amount': 'sum'})
			d1['asset'] = d1.index
			d2['asset'] = d2.index
			d3 = pd.concat([d1, d2], axis=1)
			d3 = d3.fillna(0)
			d3['ops'] = d3.quote_asset + d3.base_asset
			d3['volume'] = d3.quote_amount + d3.base_amount
			d3.sort_values('ops', ascending=False, inplace=True)
			d3['ops_day'] = d3['ops'] / self.data_days
			d3['volume_day'] = d3['volume'] / self.data_days
			d3['asset_name'] = d3.index
			d3.replace({'asset_name': self.Assets_id}, inplace=True)

			self.stats_by_token = d3

			self.stats_by_pair = df.groupby('pair').agg({'quote_amount': 'sum', 'base_amount': 'sum', 'price': 'mean', 'pair': 'count'})
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
	os.chdir('/tank/lana/bitshares/dex_hub_ev1/data')
	print("Starting")
	print("ok1")
	#a.df_ohlc[d].plot()
	#a.df_ohlc[('price', 'close')].plot()
	a=Stats()
	print('end')