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

