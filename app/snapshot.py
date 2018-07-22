"""
(c) 2017 Elias / Vanissoft

"""

import datetime
import pickle
import requests
import json

from config import Redisdb, Bitshares

Developing = False

def enqueue(dat, q):
	q.empty()
	if not Developing:
		q.enqueue_call(func=do_snapshot, args=[dat], timeout=0)
	else:
		do_snapshot(dat)


def snapshot_end_enqueue(q):
	if not Developing:
		q.enqueue_call(func=snapshot_end, args=[], timeout=0)
	else:
		snapshot_end()


def csvgen_enqueue(q):
	if not Developing:
		q.enqueue_call(func=csv_gen, args=[], timeout=0)
	else:
		csv_gen()



def obtain_balances(asset_id):
	snap_datetime = datetime.datetime.now().isoformat()
	info = pickle.loads(Redisdb.get("snapshot_info"))
	n_from = 0
	n_call = 0
	total_balance = 0
	batch_balance = 0
	total_holders = 0
	while True:
		data = {"jsonrpc": "2.0", "params": ["asset", "get_asset_holders", [info['asset_hold_id'], n_from, 100]], "method": "call",
			"id": n_call}
		try:
			rtn = requests.post('http://209.188.21.157:8090/rpc', data=json.dumps(data))
			if rtn.status_code != 200:
				return False
			rst = rtn.json()['result']
		except Exception as err:
			print(err.__repr__())
			print()
			return False
		bal = []
		to_exit = False
		for r in rst:
			amount = round(int(r['amount']) / 10 ** info['asset_hold']['precision'], info['asset_hold']['precision'])
			if amount < info['asset_hold_minimum']:
				to_exit = True
				break
			else:
				total_balance += amount
				batch_balance += amount
				total_holders += 1
				Redisdb.hset("balance:" + info['asset_hold_id'], r['account_id'],
					pickle.dumps({'account': r['account_id'], 'datetime': snap_datetime, 'amount': amount}))

		if len(rst) < 100 or to_exit:
			Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " Total count:" + str(total_holders))
			Redisdb.set("total_balance:" + info['asset_hold_id'], total_balance)
			Redisdb.set("total_owners:" + info['asset_hold_id'], total_holders)
			break
		if total_holders % 1000 == 0:
			Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " Holders: {} Balance: {} Median: {}".format(total_holders, total_balance, round(batch_balance/1000, 2)))
			batch_balance = 0

		n_from += 100
		n_call += 1
		print(n_call)
	return True



def csv_gen():
	"""
	Generate CSV files for download
	TOP 100 holders
	TAIL 100 holders
	:return:
	"""

	import csv
	from distribution import distribution_setup

	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " CSV generate list...")

	lst = distribution_setup()

	# top 1000 to csv
	lst = lst[:1000]

	snap_info = pickle.loads(Redisdb.get("snapshot_info"))

	# write to file
	fname = 'distribution_{}_{}.csv'.format(snap_info['asset_hold_id'], datetime.datetime.now().isoformat())
	with open('./web/tmp/'+fname, 'w', newline='') as fcsv:
		cw = csv.writer(fcsv, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
		cw.writerow(["Account", "Date", "Amount of "+snap_info['asset_hold']['symbol'], "Will take of "+snap_info['asset_distribute']['symbol']])
		for l in lst:
			cw.writerow(l)

	msg = "|".join([datetime.datetime.now().isoformat(), './tmp/'+fname])
	Redisdb.rpush("messages", "*|csv_exported|" + msg)

	msg = datetime.datetime.now().isoformat() + "|" + \
			"Account;Date;Amount of " + snap_info['asset_hold']['symbol'] + ";Will take of " + snap_info['asset_distribute']['symbol'] + "|"
	msg2 = ""
	for l in lst[:10]:
		for f in l:
			msg2 += f + ";"
		msg2 += "#"
	Redisdb.rpush("messages", "*|csv_data|" + msg+msg2)

	print(0)


def snapshot_end():
	# persist db to disk
	Redisdb.rpush("operations", pickle.dumps({'operation': 'db_save'}))

	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " Snapshot end")
	Redisdb.rpush("messages", "--------------")
	Redisdb.rpush("operations", pickle.dumps({'operation': 'csv_generation'}))


def do_snapshot(dat):
	if 'form' not in dat:
		return False
	if dat['form']['asset_id'] is None:
		Redisdb.rpush("messages", " Missing distribution asset")
		return False
	if dat['form']['assethold_id'] is None:
		Redisdb.rpush("messages", " Missing holding asset")
		return False
	asset_id = dat['form']['assethold_id']
	Redisdb.delete("balance:"+asset_id)
	Redisdb.delete("distribute:"+asset_id)

	Redisdb.set("total_balance:"+asset_id, 0)
	Redisdb.set("total_owners:"+asset_id, 0)
	if asset_id is None or Redisdb.get("snapshot_started") is not None:
		return False

	snap_info = {}
	snap_info['total_balance'] = 0
	snap_info['total_owners'] = 0
	snap_info['asset_hold_id'] = asset_id
	snap_info['asset_distribute_id'] = dat['form']['asset_id']
	snap_info['asset_hold'] = Bitshares.rpc.get_assets([asset_id])[0]
	snap_info['asset_hold_minimum'] = float(dat['form']['hold_minimum'])
	snap_info['asset_distribute'] = Bitshares.rpc.get_assets([dat['form']['asset_id']])[0]
	snap_info['distribution_amount'] = int(dat['form']['amount'])
	snap_info['distribution_ratio'] = float(dat['form']['ratio'])
	snap_info['distribution_minimum'] = float(dat['form']['minimum'])
	snap_info['transfer_fee'] = float(dat['form']['transfer_fee'])
	# query fees
	fees = Bitshares.rpc.get_global_properties()['parameters']['current_fees']
	Redisdb.set("snapshot_info", pickle.dumps(snap_info))

	Redisdb.rpush("messages", "*|snapshot_start")
	obtain_balances(asset_id)
	Redisdb.rpush("operations", pickle.dumps({'operation': 'snapshot_end'}))


if __name__ == "__main__":
	#Bitshares.rpc.get_asset_holder('1.3.0')
	print()