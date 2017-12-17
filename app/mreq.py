#
# (c) 2017 elias/vanissoft
#
# BUBBLE-INVESTING
#
#


import datetime
import json
import redis
import pickle

from config import Redisdb, Bitshares


def launch(data):
	"""
	Signals start distribution
	:param data:
	:return:
	"""
	Redisdb.rpush("messages", "---------------")
	Redisdb.rpush("messages", datetime.datetime.now().isoformat()+" Distribution Starts")
	data['operation'] = 'launch_distribution'
	Redisdb.rpush("operations", pickle.dumps(data))

def snapshot(data):
	"""
	Signals the start of snapshot
	:param data:
	:return:
	"""
	Redisdb.rpush("messages", "---------------")
	msg = datetime.datetime.now().isoformat()+" Snapshot Starts"
	Redisdb.rpush("messages", msg)
	data['operation'] = 'launch_snapshot'
	Redisdb.rpush("operations", pickle.dumps(data))


def get_account(acc):
	rtn = Bitshares.rpc.get_account_by_name(acc)
	if rtn is None:
		return {'td_msg': '????', 'id': None}
	else:
		rtn['td_msg'] = 'id: '+rtn['id']
	return rtn


def get_asset(ass):
	rtn = Bitshares.rpc.lookup_asset_symbols([ass])
	if rtn[0] is None:
		return {'td_msg': '????', 'id': None}
	else:
		rtn[0]['td_msg'] = 'id: '+rtn[0]['id']
	return rtn[0]


def getinfo(args, tag, path, query_string):
	"""
	http://127.0.0.1:8099/get/froga?sadf=324&asd=34
	args = {'asd': ['34'], 'sadf': ['324']} froga
	:param req: 
	:param tag: 
	:return: 
	"""
	rtn = {'data': None}
	#print("getinfo:", args, tag, path, query_string)
	if tag == 'getaccount':
		if 'account' in args:
			rtn['data'] = get_account(args['account'][0])
	elif tag == 'getasset':
		if 'asset' in args:
			rtn['data'] = get_asset(args['asset'][0])
	elif tag == 'getmessage':
		msg_arr = []
		while True:
			msg = Redisdb.lpop("messages")
			if msg is None:
				break
			msg_arr.append(msg.decode('utf8'))
			if len(msg_arr) > 100:
				break
		if len(msg_arr) > 0:
			rtn['data'] = msg_arr
	rtn['request'] = path+"?"+query_string
	return rtn


def postinfo(args, tag, path, query_string, djson):
	"""
	"""
	rtn = {}
	print("postinfo:", args, tag, path, query_string, djson)

	if tag == 'launch':
		launch(djson)
		rtn['data'] = "started"
	elif tag == 'snapshot':
		snapshot(djson)
		rtn['data'] = "started"
	rtn['request'] = path + "?" + query_string
	return json.dumps(rtn)



if __name__ == '__main__':
	print(0)

