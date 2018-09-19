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
import arrow
import pandas as pd
import passwordlock
import market_data


def clear_cache():
	"""
	Clear cached data depending on accounts
	:return:
	"""
	Redisdb.delete("balances_openpos")
	Redisdb.delete("balances_callorders")


def account_list():
	accounts = []
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


#TODO: to delete
def order_history_old(account_name):
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


def trade_history(accounts, mdf=None, module=''):
	if mdf is None:
		return False

	Accounts = []
	def data_available(df):
		import pickle
		with open('assets.pickle', 'rb') as h:
			tmp = pickle.load(h)
		Assets_id = {k: v for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}
		Assets_name = {v: k for (k, v) in [(k, v[0]) for (k, v) in tmp.items()]}

		d1 = df
		d1['pair_id'] = d1.pair
		d1['pair_text'] = d1['pair_id'].apply(lambda x: Assets_id[x.split(':')[0]] + "/" + Assets_id[x.split(':')[1]])

		rtn = Redisdb.get("settings_prefs_bases")
		if rtn is None:
			prefs = []
		else:
			prefs = json.loads(rtn.decode('utf8'))

		d1['invert'] = d1.pair_text.apply(lambda x: 1 if (prefs.index(x.split('/')[0]) if x.split('/')[0] in prefs else 999) < (prefs.index(x.split('/')[1]) if x.split('/')[1] in prefs else 998) else 0)

		d2 = d1.loc[(d1.invert==1)]
		d2[['pays_amount', 'receives_amount']] = d2[['receives_amount', 'pays_amount']]
		d2[['price']] = 1/d2[['price']]
		d2.pair_id = d2.pair_id.apply(lambda x: x.split(':')[1]+":"+x.split(':')[0])
		d2.pair_text = d2.pair_text.apply(lambda x: x.split('/')[1]+"/"+x.split('/')[0])
		d2.index = d2.pair_id

		d3 = d1.loc[(d1.invert==0)]
		d4 = pd.concat([d2, d3])
		d4.sort_values('block_time', ascending=False, inplace=True)
		d4['time'] = d4.block_time.apply(lambda x: arrow.get(x).isoformat()[:-6])
		d4['account'] = d4.account_id.apply(lambda x: Accounts[x])
		d4['type'] = d4.invert.apply(lambda x: 'SELL' if x==0 else 'BUY')
		resp = [z for z in zip(d4.time.tolist(), d4.account.tolist(), d4.type.tolist(), d4.pair_text.tolist(),
							   d4.price.tolist(), d4.pays_amount.tolist(), d4.receives_amount.tolist())]
		Redisdb.rpush("datafeed", json.dumps({'module': module, 'data': json.dumps(resp)}))

	rtn = Redisdb.get("settings_accounts")
	if rtn is None:
		return False
	else:
		tmp = json.loads(rtn.decode('utf8'))
		Accounts = {v[3]:v[0] for v in tmp}
	market_data.Account_data(accounts, 30, mdf, data_available)
	Redisdb.rpush('operations_bg', json.dumps({'call': 'marketdatafeeder_step', 'module': 'general'}))


if __name__ == '__main__':
	#order_history(account)
	pass
