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
from cryptography.fernet import Fernet



def clear_cache():
	"""
	Clear cached data depending on accounts
	:return:
	"""
	Redisdb.delete("balances_openpos")
	Redisdb.delete("balances_callorders")


def account_list(master_unlocked, master_passwd):
	rtn = None
	accounts = []
	if rtn is None:
		rtn = Redisdb.get("settings_accounts")
		if rtn is not None and rtn.decode('utf8') != 'null':
			accounts = json.loads(rtn.decode('utf8'))
			if master_unlocked and master_passwd is not None:
				cipher = Fernet(master_passwd)  # cipher with master key hash
				for ac in accounts:
					try:
						ac[2] = cipher.decrypt(ac[2].encode('utf8')).decode('utf8')
					except:
						ac[2] = "*error unlocking*"
			else:
				for ac in accounts:
					ac[2] = "*locked*"
	return accounts


def account_new(data, passwd):
	dat = data['data']
	rtn = Redisdb.get("settings_accounts")
	if rtn is None or rtn.decode('utf8') == 'null':
		accounts = []
	else:
		accounts = json.loads(rtn.decode('utf8'))
	tmp = Bitshares.rpc.get_account(dat[0])
	if tmp is None:
		Redisdb.rpush("datafeed", json.dumps({'message': "Account doesn't exists<br><strong>"+dat[0]+"</strong>", 'error': True}))
		return
	account_id = tmp['id']
	dat.append(account_id)
	cipher = Fernet(passwd)  # cipher with master key hash
	dat[2] = cipher.encrypt(dat[2].encode('utf8')).decode()
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

