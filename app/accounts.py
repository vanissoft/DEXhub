#
#
# (c) 2017 elias/vanissoft
#
# Bitshares comm
#
"""
"""




from config import *
import json
import passwordlock



def clear_cache():
	"""
	Clear cached data depending on accounts
	:return:
	"""
	Redisdb.delete("balances_openpos")
	Redisdb.delete("balances_callorders")


def account_list():
	rtn = None
	accounts = []
	if rtn is None:
		rtn = Redisdb.get("settings_accounts")
		if rtn is not None and rtn.decode('utf8') != 'null':
			accounts = json.loads(rtn.decode('utf8'))
			if Redisdb.get('master_hash') is None:
				for ac in accounts:
					ac[2] = '*locked*'
			else:
				for ac in accounts:
					try:
						tmp = passwordlock.decrypt_data(ac[2])
						if tmp is not None:
							ac[2] = tmp
					except:
						ac[2] = "*error unlocking*"
	return accounts


def account_new(data):
	dat = data['data']
	rtn = Redisdb.get("settings_accounts")
	if rtn is None or rtn.decode('utf8') == 'null':
		accounts = []
	else:
		accounts = json.loads(rtn.decode('utf8'))
	tmp = Bitshares.rpc.get_account(dat[0])
	if tmp is None:
		Redisdb.rpush("datafeed", json.dumps({'module':'general', 'message': "Account doesn't exists<br><strong>"+dat[0]+"</strong>", 'error': True}))
		return
	if Redisdb.get('master_hash') is None:
		Redisdb.rpush("datafeed", json.dumps({'module':'general', 'message': "Unlock first", 'error': True}))
		return
	account_id = tmp['id']
	dat.append(account_id)
	dat[2] = passwordlock.encrypt_data(dat[2])
	accounts.append(dat)
	clear_cache()
	return accounts

def account_delete(data):
	id = data['id']
	rtn = Redisdb.get("settings_accounts")
	if rtn is None:
		accounts = []
	else:
		accounts = json.loads(rtn.decode('utf8'))
		accounts.pop(id)
		Redisdb.set("settings_accounts", json.dumps(accounts))
	clear_cache()
	return accounts


def order_history(account_name):
	#TODO: nodes keep a max history of 1000 trades
	"""
	{'id': '1.11.362687717',
	'op': [4, {'fee': {'amount': 25921, 'asset_id': '1.3.113'},
			'order_id': '1.7.145256531', 'account_id': '1.2.203202',
			'pays': {'amount': 202507354, 'asset_id': '1.3.0'},
			'receives': {'amount': 25921671, 'asset_id': '1.3.113'},
			'fill_price': {'base': {'amount': 330800000, 'asset_id': '1.3.0'},
			'quote': {'amount': 42343592, 'asset_id': '1.3.113'}},
			'is_maker': True}], 'result': [0, {}], 'block_num': 29179328, 'trx_in_block': 19, 'op_in_trx': 0, 'virtual_op': 8617}

	:param account_name:
	:return:
	"""
	#TODO:

	from bitshares.account import Account
	#TODO: ensure_full warrants full history?
	Account(account_name).ensure_full()
	movs = [x for x in Account(account_name).history(only_ops=['fill_order'])]
	print(0)


def trade_history(account_name):
	from bitshares.account import Account
	id = Account(account_name).identifier


if __name__ == '__main__':
	#order_history(account)
	pass
