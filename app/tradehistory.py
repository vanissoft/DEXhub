#
# (c) 2018 elias/vanissoft
#
'''


'''

from multiprocessing import Process

import datetime
import arrow
import requests

import json
import pandas as pd

from collections import namedtuple

import redis

PROCESS_NUM = 8

hdrs = {'Host': 'graphs.coinmarketcap.com',
		'User-Agent': 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/56.0.2924.76 Chrome/56.0.2924.76 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Encoding': 'gzip,deflate,sdch', 'Accept-Language': 'en-US,en;q=0.8'}


def redisdb():
	return redis.StrictRedis(host='127.0.0.1', port=6383, db=1)

def read_trade_history():
	Redisdb = redisdb()
	task = Redisdb.lpop("queue")
	if task is None:
		return
	date_range = json.loads(task.decode('utf8'))
	date_range = list(map(lambda x: x.split('+')[0], date_range))
	if Redisdb.hget("loaded", date_range) is not None:
		return
	rec_number = 1000
	print("range:", date_range, end='')
	data = None

	#rq = 'http://185.208.208.184:5000/' + \
	#rq = 'https://eswrapper.bitshares.eu/' + \
	rq = 'http://95.216.32.252:5000/' + \
	'get_account_history?operation_type=4&size=1000&' +\
			'from_date={}&to_date={}&'.format(*date_range) +\
			'sort_by=-block_data.block_time&type=data&agg_field=operation_type'

	rtn2 = requests.get(rq, headers=hdrs)

	op_list = json.loads(rtn2.content.decode('utf8'))
	order = namedtuple('order_filled', ['block_num', 'block_time', 'order_id', 'account_id', 'is_maker',
										'pays_asset', 'pays_amount', 'receives_asset', 'receives_amount'])
	order_list = []
	print(" results ", end='')
	for op in op_list:
		block_number = op['block_data']['block_num']
		block_time = op['block_data']['block_time']
		otr = json.loads(op['operation_history']['op'])
		ot = otr[1]
		order_list.append(order._make([block_number, block_time, ot['order_id'], ot['account_id'], ot['is_maker'],
									   ot['pays']['asset_id'], ot['pays']['amount'],
									   ot['receives']['asset_id'], ot['receives']['amount'],
									   ]))
	Redisdb.lpush('data', json.dumps(order_list))
	Redisdb.hset("loaded", date_range, 1)

	if len(order_list) > 0:
		first = arrow.get(order_list[-1].block_time).datetime

	# add new range
	if len(order_list) < rec_number:
		pass
	else:
		Redisdb.lpush('queue', json.dumps((arrow.get(date_range[0]).datetime.isoformat().split('+')[0], first.isoformat().split('+')[0])))
	print(' data_len:', str(Redisdb.llen("data")), " queue_len:", str(Redisdb.llen('queue')))




def setup(dfrom=None, days=0, hours=1):
	import subprocess, time
	proc1 = subprocess.Popen("redis-server --port 6383", shell=True)
	while True:
		try:
			Redisdb = redisdb()
			# cleanup
			Redisdb.delete('queue')
			break
		except:
			time.sleep(1)

	if dfrom is None:
		from glob import glob
		lastf = glob('*.parquet')
		if len(lastf) > 0:
			lastf.sort(reverse=True)
			df = pd.read_parquet(lastf[0])
			last = df.block_time.max()
			print("last:", last)
		else:
			last = None
	else:
		last = None


	hours = 1
	if dfrom is None:
		tto = arrow.utcnow().datetime.replace(tzinfo=None)
	else:
		tto = dfrom.replace(tzinfo=None)
	if last is not None:
		tbottom = arrow.get(last).datetime.replace(tzinfo=None)
	else:
		tbottom = tto - datetime.timedelta(days=days)
	tfrom = tto - datetime.timedelta(hours=hours)
	print('tto:', tto, 'tbottom:', tbottom, 'tfrom:', tfrom)
	while tfrom >= (tbottom-datetime.timedelta(hours=hours)):
		Redisdb.rpush('queue', json.dumps((tfrom.isoformat(), tto.isoformat())))
		# dat = json.loads(op.decode('utf8'))
		tto = tfrom
		tfrom = tto - datetime.timedelta(hours=hours)
	Redisdb.set("current", "data+" + tfrom.isoformat())


def start():
	Redisdb = redisdb()
	Redisdb.delete("data")
	Redisdb.delete('loaded')
	while True:
		procs = [Process(target=read_trade_history) for x in range(PROCESS_NUM)]
		for p in procs:
			p.start()
		for p in procs:
			p.join()
		if Redisdb.llen("queue") == 0:
			break
	Redisdb.bgsave()
	print("end of work")
	print("data len:", Redisdb.llen("data"))
	print("queue:", Redisdb.llen("queue"))


def postProcess1(from_idx=0, to_idx=0):
	Redisdb = redisdb()
	order = namedtuple('order_filled', ['block_num', 'block_time', 'order_id', 'account_id', 'is_maker',
										'pays_asset', 'pays_amount', 'receives_asset', 'receives_amount'])
	df = None
	ind = from_idx
	batch = []
	while True:
		tmp = Redisdb.lindex("data", ind)
		if tmp is None:
			break
		batch.append(tmp)
		ind += 1
		if to_idx > 0  and ind > to_idx:
			break
		print(ind, " ", end='')

	print()
	print("load dataframe......", end=' ')
	data_list = []
	for data in batch:
		data = json.loads(data.decode('utf8'))
		print(".", end='')
		for d in data:
			data_list.append(order._make(d))
	df = pd.DataFrame(data_list)
	print("ok")
	print("date_range:", df.block_time.min(), df.block_time.max())

	if df is None:
		print("Nothing to do")
		return
	#order = namedtuple('order_filled', ['block_num', 'block_time', 'order_id', 'account_id', 'is_maker',
	#									'pays_asset', 'pays_amount', 'receives_asset', 'receives_amount'])
	print("drop duplicates", end=' ')
	df = df.drop_duplicates()
	print("ok")
	print("various", end=' ')
	df[['pays_amount', 'receives_amount']] = df[['pays_amount', 'receives_amount']].apply(pd.to_numeric)
	df[['block_time']] = df[['block_time']].apply(pd.to_datetime)
	df[['pays_asset', 'receives_asset']] = df[['pays_asset', 'receives_asset']].astype('category')
	print("ok")
	print("create pair", end=' ')
	df['pair'] = df[['pays_asset', 'receives_asset']].apply(lambda x: ':'.join(x), axis=1)
	df[['pair']] = df[['pair']].astype('category')
	print("ok")
	return df


def postProcess2(df):
	import pickle
	from bitshares.asset import Asset
	try:
		with open('assets.pickle', 'rb') as h:
			assets = pickle.load(h)
	except:
		assets = {}

	s1 = set(df.pays_asset.value_counts().index.tolist())
	s2 = set(df.receives_asset.value_counts().index.tolist())
	s1.update(s2)

	# for dropping unpopular pairs
	if False:
		df['popular_pair'] = False
		df.loc[(df['pays_asset'].isin(s1)) & (df['receives_asset'].isin(s1)), 'popular_pair'] = True
		df.drop(df[df['popular_pair'] == False].index, inplace=True)

	# TODO: there were not all assets in pickle file with this code
	for s in s1:
		if s in assets:
			asset_symbol, asset_precision = assets[s]
			print(".", end=' ')
		else:
			a2 = Asset(s)
			assets[s] = [a2.symbol, a2.precision]
			asset_symbol, asset_precision = [a2.symbol, a2.precision]
			print("new", end=' ')
		print(asset_symbol)
		# drop minimal trades (dust?)
		if False:
			dust_threshold = 1e5 / 10**asset_precision
			df.drop(df[(df['pays_asset'] == s) & (df['pays_amount'] < dust_threshold)].index, inplace=True)
			df.drop(df[(df['receives_asset'] == s) & (df['receives_amount'] < dust_threshold)].index, inplace=True)

		df.loc[df['pays_asset']==s, 'pays_amount'] /= (10 ** asset_precision)
		df.loc[df['receives_asset'] == s, 'receives_amount'] /= (10 ** asset_precision)

	with open('assets.pickle', 'wb') as h:
		pickle.dump(assets, h)


	df['price'] = -1
	# popular pairs are ok
	df['price'] = df['receives_amount'] / df['pays_amount']
	#df = df.set_index('block_time')

	print(0)
	date_from = df.block_time.min()
	date_to = df.block_time.max()
	print("save to parquet", len(df), end=' ')
	df.to_parquet('bts_trades_{}_{}.curated.parquet'.format(date_from, date_to), 'fastparquet', 'GZIP')

	print("ok")
	print("end of work")


def postProcess3():
	import os
	from glob import glob
	files = glob("*.curated.parquet")
	df = []
	for f in files:
		print(f)
		df.append(pd.read_parquet(f))
	df2 = pd.concat(df)
	if len(df) > 1:
		df2 = df2.drop_duplicates()

	print("postprocess 3")
	print("date range:", df2.block_time.min(), df2.block_time.max())
	df2['date'] = df2.block_time.dt.date
	dates = df2['date'].unique().tolist()
	df2.drop(['date'], axis=1, inplace=True)
	for dat in dates:
		file = glob('*{:04d}{:02d}{:02d}.parquet'.format(dat.year, dat.month, dat.day))
		if len(file) == 1:
			file = file[0]
			df3 = pd.read_parquet(file)
		else:
			df3 = None
			file = 'bts_trades_{:04d}{:02d}{:02d}.parquet'.format(dat.year, dat.month, dat.day)
		last = arrow.get(dat.year, dat.month, dat.day).isoformat()
		next = arrow.get(dat.year, dat.month, dat.day).shift(days=1)
		df1 = df2.loc[(df2.block_time >= last) & (df2.block_time < next.isoformat())]
		print("date:", dat, "range:", last, next)
		if len(df1) > 0:
			if df3 is not None:
				print("concatenating")
				df4 = pd.concat((df3,df1))
				df4 = df4.drop_duplicates()
				print("length", len(df4))
				df4.to_parquet(file+".hot", 'fastparquet', 'GZIP')
			else:
				print("overwrite")
				df1.to_parquet(file+".hot", 'fastparquet', 'GZIP')
			os.rename(file+".hot", file)
	if len(files)>0:
		for f in files:
			os.remove(f)


def tmp_split():
	from glob import glob
	files = glob('bts_trades_2018*.parquet')
	for f in files:
		if len(f) > 25:
			continue
		df = pd.read_parquet(f)
		df['date'] = df.block_time.dt.date
		dates = df['date'].unique().tolist()
		df.drop(['date'], axis=1, inplace=True)
		for dat in dates:
			file = glob('*{:04d}{:02d}{:02d}.parquet'.format(dat.year, dat.month, dat.day))
			if len(file) == 1:
				file = file[0]
				df3 = pd.read_parquet(file)
			else:
				df3 = None
				file = 'bts_trades_{:04d}{:02d}{:02d}.parquet'.format(dat.year, dat.month, dat.day)
			last = arrow.get(dat.year, dat.month, dat.day).isoformat()
			next = arrow.get(dat.year, dat.month, dat.day).shift(days=1)
			df1 = df.loc[(df.block_time >= last) & (df.block_time < next.isoformat())]
			print("date:", dat, "range:", last, next)
			if len(df1) > 0:
				if df3 is not None:
					print("concatenating")
					df4 = pd.concat((df3,df1))
					df4 = df4.drop_duplicates()
					print("length", len(df4))
					df4.to_parquet(file+".hot", 'fastparquet', 'GZIP')
				else:
					print("overwrite")
					df1.to_parquet(file+".hot", 'fastparquet', 'GZIP')
				os.rename(file+".hot", file)

if __name__ == "__main__":
	import sys
	import os
	os.chdir('../data')
	if len(sys.argv) > 1:
		print(sys.argv)
	print("Starting")
	#tmp_split()
	setup()
	#setup(arrow.get('2018-08-01'), 7)
	start()
	df = postProcess1()
	postProcess2(df)
	postProcess3()
