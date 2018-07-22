"""
(c) 2017 Elias / Vanissoft

"""

from time import sleep
import datetime
import pickle

from config import Redisdb, Bitshares

Developing = False

def enqueue(dat, q):
	q.empty()
	if not Developing:
		q.enqueue_call(func=do_distribution, args=[dat], timeout=0)
	else:
		do_distribution(dat)

def batch_enqueue(dat, q):
	if not Developing:
		q.enqueue_call(func=do_batch, args=[dat], timeout=0)
	else:
		do_batch(dat)

def endcheck_enqueue(q):
	if not Developing:
		q.enqueue_call(func=end_check, args=[], timeout=0)
	else:
		end_check()



def do_batch(dat):
	"""
	Make a batch of transfers
	:param dat:
	:return:
	"""
	import config
	snap_info = pickle.loads(Redisdb.get("snapshot_info"))
	# TODO: obtener la cuenta a partir de la clave pública
	# TODO: obtener balance de la moneda a repartir y de la moneda del fee
	#
	try:
		Bitshares = config.BitShares(node=config.WSS_NODE, wif=dat['key'])
	except Exception as err:
		print(err.__repr__())
		Redisdb.rpush("messages", "*|launch_error|key not found")
		print(0)
		return False

	for job in dat['job']:
		try:
			test = Bitshares.transfer(job[0].decode('utf8'), float(job[1]), dat['asset'], "", "1.2.4411")
		except Exception as err:
			print(err.__repr__())
			print(0)

	Redisdb.decr("batch_jobs", int(1))
	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " Jobs queue: {}".format(int(Redisdb.get("batch_jobs"))))





def end_check():
	"""
	Check for the finalization of snapshot tasks
	:param dat:
	:param q:
	:return:
	"""
	while True:
		print("snap_end", Redisdb.get("batch_jobs"))
		if int(Redisdb.get("batch_jobs")) == 0:
			# persist db to disk
			Redisdb.rpush("operations", pickle.dumps({'operation': 'db_save'}))

			Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " Distribution end")
			Redisdb.rpush("messages", "--------------")
			break
		sleep(2)



def distribution_setup():
	"""
	Makes a preview of the distribution
	:return:
	"""
	snap_info = pickle.loads(Redisdb.get("snapshot_info"))
	holders = Redisdb.hgetall("balance:"+snap_info['asset_hold_id'])
	lst = []
	cnt = 0
	balance = 0
	for h in holders:
		hdata = pickle.loads(holders[h])
		lst.append([hdata['account'], hdata['datetime'], hdata['amount'], 0])
		balance += hdata['amount']
		cnt += 1
		if cnt % 1000 == 0:
			Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " CSV list "+str(cnt))

	# refresh snapshot info
	snap_info['total_balance'] = balance
	snap_info['total_owners'] = int(Redisdb.get("total_owners:"+snap_info['asset_hold_id']))
	Redisdb.set("snapshot_info", pickle.dumps(snap_info))

	msg = "|".join([datetime.datetime.now().isoformat(), str(int(snap_info['total_balance'])), \
			str(int(snap_info['total_owners'])), str(int(snap_info['total_owners']*snap_info['transfer_fee']))])
	Redisdb.rpush("messages", "*|snapshot_end|" + msg)

	# The list is sorted from more to less holding
	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " CSV list sorting")
	lst.sort(key=lambda x: x[2], reverse=True)
	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + " CSV list sorting OK")

	# calculus of the distribution
	tmplt_distr = "{0:."+str(snap_info['asset_distribute']['precision'])+"f}"
	tmplt_hold = "{0:."+str(snap_info['asset_hold']['precision'])+"f}"
	total_distr_amount = 0
	for l in enumerate(lst):
		if snap_info['distribution_amount'] > 0:
			amount = round(l[1][2] / balance * snap_info['distribution_amount'], snap_info['asset_distribute']['precision'])
		elif snap_info['distribution_ratio'] > 0:
			amount = round(l[1][2] * snap_info['distribution_ratio'], snap_info['asset_distribute']['precision'])
		if amount < snap_info['distribution_minimum']:
			# truncate the list
			lst = lst[:l[0]]
			break
		total_distr_amount += amount
		lst[l[0]][3] = tmplt_distr.format(amount)
		lst[l[0]][2] = tmplt_hold.format(l[1][2])

	# feed the distribution container
	for l in lst:
		Redisdb.hset("distribute:" + snap_info['asset_hold_id'], l[0], l[3])

	if snap_info['distribution_amount'] > 0:
		rest = snap_info['distribution_amount'] - total_distr_amount
	else:
		rest = 0
	# TODO: what to do with the rest?

	return lst



def do_distribution(dat):
	"""
	Makes the actual transfer of tokens.
	The snapshoting step have to be done before this.
	:return:
	"""

	import config
	try:
		wallet = config.BitShares(node=config.WSS_NODE, wif=dat['form']['key'])
		ga = wallet.wallet.getAccounts()
		print(ga)
	except Exception as err:
		print(err.__repr__())
		Redisdb.rpush("messages", "*|launch_error|key not found")
		print(0)
		return False


	snap_info = pickle.loads(Redisdb.get("snapshot_info"))
	Redisdb.rpush("messages", "--------------")
	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + "Distribution started")

	batch_count = 0
	batch = []
	lst = list(Redisdb.hgetall("distribute:"+snap_info['asset_hold_id']).items())
	while True:
		distr = lst.pop(0)
		batch_count += 1
		batch.append(distr)
		if batch_count > 100 or len(lst) == 0:
			op_dat = {'operation': 'distribution_batch', 'job': batch, 'key': dat['form']['key'], 'asset': snap_info['asset_distribute']['symbol']}
			Redisdb.rpush("operations", pickle.dumps(op_dat))
			Redisdb.incr("batch_jobs", 1)
			if len(lst) == 0:
				break
	Redisdb.rpush("messages", datetime.datetime.now().isoformat() + "Jobs generated")
	Redisdb.rpush("operations", pickle.dumps({'operation': 'distribution_check'}))

if __name__ == "__main__":
	print()