#
#
# (c) 2017 elias/vanissoft
#
# Bitshares comm
#
"""
	cols = "id,issuer,dynamic_asset_data_id,symbol,precision,description_main,description_market,\
			description_short_name,market_fee_percent,issuer_permissions,flags,max_supply,options".split(",")

	p.hset("asset1:" + b['symbol'], k, json.dumps(b[k]))
	p.hset("asset2:" + b['id'], k, json.dumps(b[k]))

	Store of data:
		Redisdb.set("open_positions", json.dumps(ob))
		hset("market_history:BRIDE/BTS", "2017-11-27", "123123.232@232.23")
		Redisdb.set("settings_accounts", json.dumps(accounts))
		"balances"


	Progress indicators:
		Redisdb.set("status:loading_assets", 0)
		set("status:market:BRIDGE/BTS", "FIRST|LAST")

	Bus:
		Redisdb.rpush("datafeed", json.dumps({'orderbook': {'market': mkt, 'date': arrow.utcnow().isoformat(), 'data': buys}}))


	RPC calls
	=========
	Last trades:
		Bitshares.rpc.get_fill_order_history("1.3.121", "1.3.0", 100, api_id=3)
		{'id': '0.0.10874385',
			'op': {'fee': {'amount': 0, 'asset_id': '1.3.0'},
					'account_id': '1.2.126225', 'order_id': '1.7.42662694',
					'pays': {'amount': 20953, 'asset_id': '1.3.121'},
					'receives': {'amount': 1197306, 'asset_id': '1.3.0'}},
			'key': {'base': '1.3.0', 'sequence': -1081491, 'quote': '1.3.121'},
			'time': '2017-12-11T10:11:45'}

	Account history:
		Bitshares.rpc.get_account_history("1.2.203202", "1.11.99", 100, "1.11.0", api_id=3)
			# place order
			[{'trx_in_block': 1, 'op_in_trx': 0, 'id': '1.11.102636158',
				'op': [1, {'extensions': [], 'seller': '1.2.203202',
						'fee': {'amount': 1213, 'asset_id': '1.3.0'},
						'fill_or_kill': False,
						'amount_to_sell': {'amount': 37149320, 'asset_id': '1.3.1093'},
						'min_to_receive': {'amount': 3529185, 'asset_id': '1.3.121'},
						'expiration': '2022-12-11T10:07:37'}],
				'virtual_op': 15417, 'result': [1, '1.7.42662747'], 'block_num': 22554386},
			# place order
			{'trx_in_block': 1, 'op_in_trx': 0, 'id': '1.11.102636105',
				'op': [1, {'extensions': [], 'seller': '1.2.203202',
						'fee': {'amount': 1213, 'asset_id': '1.3.0'},
						'fill_or_kill': False,
						'amount_to_sell': {'amount': 30000000, 'asset_id': '1.3.1093'},
						'min_to_receive': {'amount': 1060499, 'asset_id': '1.3.121'},
						'expiration': '2022-12-11T10:07:03'}],
				'virtual_op': 15304, 'result': [1, '1.7.42662720'], 'block_num': 22554375},
			# cancel order
			{'trx_in_block': 1, 'op_in_trx': 0, 'id': '1.11.102635933',
				'op': [2, {'fee': {'amount': 121, 'asset_id': '1.3.0'}, 'extensions': [],
						'order': '1.7.42662012', 'fee_paying_account': '1.2.203202'}],
				'virtual_op': 14876, 'result': [2, {'amount': 67149320, 'asset_id': '1.3.1093'}], 'block_num': 22554358},
			# place order
			{'trx_in_block': 1, 'op_in_trx': 0, 'id': '1.11.102633852',
				'op': [1, {'extensions': [], 'seller': '1.2.203202', 'fee': {'amount': 1213, 'asset_id': '1.3.0'},
							'fill_or_kill': False,
							'amount_to_sell': {'amount': 67149320, 'asset_id': '1.3.1093'},
							'min_to_receive': {'amount': 2283076, 'asset_id': '1.3.121'},
							'expiration': '2022-12-11T09:50:25'}],
				'virtual_op': 10097, 'result': [1, '1.7.42662012'], 'block_num': 22554063},
			# fill order
			{'trx_in_block': 7, 'op_in_trx': 2, 'id': '1..102633818',
				'op': [4, {'fee': {'amount': 902, 'asset_id': '1.3.1093'},
							'account_id': '1.2.203202',
							'order_id': '1.7.42661962',
							'pays': {'amount': 27980, 'asset_id': '1.3.121'},
							'receives': {'amount': 902581, 'asset_id': '1.3.1093'}}],
					'virtual_op': 10024, 'result': [0, {}], 'block_num': 22554057},

	Balances:
		Bitshares.rpc.get_account_balances(BTS_ACCOUNT_ID, [])
			[{'asset_id': '1.3.0', 'amount': 1144690707},
			{'asset_id': '1.3.743', 'amount': 496859},
			{'asset_id': '1.3.822', 'amount': '8214856726'},
			{'asset_id': '1.3.858', 'amount': 1414936},
			{'asset_id': '1.3.861', 'amount': 5231},
			{'asset_id': '1.3.1042', 'amount': 1},
			{'asset_id': '1.3.1093', 'amount': 49499},
			{'asset_id': '1.3.1152', 'amount': 4892075},
			{'asset_id': '1.3.1325', 'amount': 17723532},
			{'asset_id': '1.3.1564', 'amount': '7646023351'},
			{'asset_id': '1.3.1999', 'amount': 182362526},
			{'asset_id': '1.3.2298', 'amount': 40},
			{'asset_id': '1.3.2379', 'amount': 250}]


"""

from config import *
import asyncio
import json
import arrow
import random
from cryptography.fernet import Fernet
import hashlib
import base64
from bitshares import BitShares
import blockchain
import pickle
import os

WBTS = None
Assets = {}
Assets_id = {}
Assets_name = {}



def load_assets():
	global Assets, Assets_id, Assets_name
	if len(Assets_id) > 0:
		return
	os.chdir('../data')
	with open('assets.pickle', 'rb') as h:
		tmp = pickle.load(h)
	Assets = {k: v for (k, v) in [(k, v) for (k, v) in tmp.items()]}
	Assets_id = {k:v for (k,v) in [(k,v[0]) for (k,v) in tmp.items()]}
	Assets_name = {v:k for (k,v) in [(k,v[0]) for (k,v) in tmp.items()]}


def init():
	"""
	Initialisation
	*
	:return:
	"""
	#load_assets()
	print("end loading assets")



def blockchain_listener():
	"""
	Execute forever listening blockchain operations
	:return:
	"""
	from bitshares.blockchain import Blockchain
	chain = Blockchain()
	for block in chain.blocks():
		#print("listenet:", block)
		Redisdb.rpush("bitshares_op", pickle.dumps(block))


async def read_ticker(market, force=False):
	rtn = Redisdb.get("ticker_"+market)
	if rtn is not None and not force:
		return json.loads(rtn.decode('utf8'))
	pair = market.split("/")
	if pair[0] == pair[1]:
		return [1,0,0]
	# BTS/USD get ticker of BTS with prices in USD
	rtn = Bitshares.rpc.get_ticker(pair[1], pair[0])
	price = float(rtn['highest_bid'])
	chg_24h = float(rtn['percent_change'])
	volume = float(rtn['base_volume'])
	rtn = [price, volume, chg_24h]
	Redisdb.setex("ticker_"+market, random.randint(200, 500), json.dumps(rtn))
	return rtn


async def account_list():
	rtn= Redisdb.get("settings_accounts")
	if rtn is None:
		accounts = []
	else:
		accounts = json.loads(rtn.decode('utf8'))
	return accounts


async def read_balances():

	alist = await account_list()
	if len(alist) == 0:
		return None

	while True:  # enable reenter due new assets
		bal = {}
		for account in alist:
			bal[account[0]] = {}
			try:
				rtn = Bitshares.rpc.get_account_balances(account[3], [])
			except Exception as err:
				rtn = []
				print(err.__repr__())
			for r in rtn:
				try:
					prec = int(Redisdb.hget("asset2:" + r['asset_id'], 'precision'))
				except:
					Redisdb.rpush("datafeed", json.dumps({'module': "general", 'message': "New assets!", 'error': False}))
					load_assets()  # reread new assets
					continue
				symbol = Redisdb.hget("asset2:" + r['asset_id'], 'symbol').decode('utf8')
				amount = round(int(r['amount']) / 10 ** prec, prec)
				if amount > 0:
					bal[account[0]][symbol] = [amount, 0]
		break
	Redisdb.setex("cache_balances", random.randint(200, 3000), json.dumps(bal))
	return bal




async def get_balances():
	# TODO: another column for asset collateral
	"""
	Return balance consolidated with "balances_openpos"
	"""
	global Assets
	load_assets()
	#return None
	accounts = await account_list()
	bal1 = await read_balances()
	if bal1 is None:
		return None, None, None
	bal2 = Redisdb.get("balances_openpos")
	if bal2 is None:
		rtn = await open_positions()
		bal2 = Redisdb.get("balances_openpos")
	bal2 = json.loads(bal2.decode('utf8'))
	# bal2: [[account, order_id, pair, buy or sell, amount1, asset_id2, amount2, asset_id2, price, decs1, decs2
	for b in bal2:
		if b[3] != 'sell':
			continue
		token = b[2].split('/')[0]
		account = b[0]
		if token in bal1[account]:
			bal1[account][token] = [bal1[account][token][0], b[4]]
		else:
			bal1[account][token] = [0, b[4]]

	base = await read_ticker("BTS/USD")
	#return [mid_price, volume, chg_24h]
	for account in bal1:
		for b in bal1[account]:
			if 'VYI' in b:
				print()
			tick = await read_ticker(b+"/BTS")
			for t in enumerate(tick):
				if t[1] == float('Infinity'):
					tick[t[0]] = 0
			bal1[account][b].append([tick[0]*base[0], tick[1]*base[0], tick[2], int(Assets[Assets_name[b]][1])])

	margin_lock_BTS = {}
	margin_lock_USD = {}
	bal3 = Redisdb.get("balances_callorders")
	if bal3 is not None:
		bal3 = json.loads(bal3.decode('utf8'))
		for b in bal3:
			tick = await read_ticker(b[1]+"/BTS")
			for t in enumerate(tick):
				if t[1] == float('Infinity'):
					tick[t[0]] = 0
				# assume that collateral is always BTS and value in USD
			if b[0] in margin_lock_BTS:
				margin_lock_BTS[b[0]] += b[4]
			else:
				margin_lock_BTS[b[0]] = b[4]
			if b[0] in margin_lock_USD:
				margin_lock_USD[b[0]] += (b[4] * base[0]) -  (b[2] * tick[0] * base[0])
			else:
				margin_lock_USD[b[0]] = (b[4] * base[0]) -  (b[2] * tick[0] * base[0])

	return (bal1, margin_lock_BTS, margin_lock_USD)


async def get_orderbook(data):
	global Assets, Assets_id
	load_assets()
	mkt = data['market']
	pairs = mkt.split("/")
	p1 = Assets_name[pairs[0]]
	p2 = Assets_name[pairs[1]]
	rtn = Bitshares.rpc.get_limit_orders(p1, p2, 5000)

	dat = []
	for pos in rtn:
		if p1 == pos['sell_price']['quote']['asset_id']:  # buy
			amount_base = int(pos['sell_price']['base']['amount']) / 10 ** Assets[p2][1]
			amount_quote = int(pos['sell_price']['quote']['amount']) / 10 ** Assets[p1][1]
			price = round(amount_base / amount_quote, Assets[p2][1])
			total = round(amount_quote * price, Assets[p2][1])
			op = 'buy'
		else:  # sell
			amount_base = int(pos['sell_price']['base']['amount']) / 10 ** Assets[p1][1]
			amount_quote = int(pos['sell_price']['quote']['amount']) / 10 ** Assets[p2][1]
			price = round(amount_quote / amount_base, Assets[p2][1])
			total = round(amount_base*price, Assets[p2][1])
			op = 'sell'
		dat.append([op, price, total])
	buys = [x for x in dat if x[0]=='buy']
	buys.sort(key=lambda x: x[1], reverse=True)
	best_offer = 0.00001
	if len(buys) > 0:
		best_offer = buys[0][1]
	acum = 0
	for x in buys:
		acum += x[2]
		x.append(acum)
	buys.sort(key=lambda x: x[3], reverse=True)

	sells = [x for x in dat if x[0]=='sell']
	sells.sort(key=lambda x: x[1], reverse=False)
	acum = 0
	for x in sells:
		acum += x[2]
		x.append(acum)
	sells.sort(key=lambda x: x[3], reverse=False)

	buys.extend([s for s in sells if s[1] < best_offer * 5])
	buys.sort(key=lambda x: x[1])

	return buys


async def delete_open_positions():
	global Assets
	alist = await account_list()
	if alist is None or len(alist) == 0:
		return None
	load_assets()

	ob = {}
	for account in alist:
		ob[account[0]] = []
		try:
			account_data = Bitshares.rpc.get_full_accounts([account[0]], False)[0][1]
		except:
			continue
		# read call orders
		if Redisdb.get("balances_callorders") is None or True:
			call_orders = []
			for co in account_data['call_orders']:
				quote = co['call_price']['quote']['asset_id']
				base = co['call_price']['base']['asset_id']
				try:
					amount_debt = round(int(co['debt']) / 10 ** Assets[quote][1], Assets[quote][1])
					amount_collateral = round(int(co['collateral']) / 10 ** Assets[base][1], Assets[base][1])
					call_orders.append([account[0], Assets[quote][0], amount_debt, Assets[base][0], amount_collateral])
				except Exception as err:
					print(err.__repr__())
			if len(call_orders) > 0:
				#TODO: without use?
				Redisdb.setex("balances_callorders", 300, json.dumps(call_orders))

		base_coins = 'BTS,USD,CNY,RUB,EUR'.split(",")
		for lo in account_data['limit_orders']:
			quote = lo['sell_price']['quote']['asset_id']
			base = lo['sell_price']['base']['asset_id']
			date = arrow.get(lo['expiration']).shift(years=-5).isoformat()
			try:
				amount_quote = round(int(lo['sell_price']['quote']['amount']) / 10 ** Assets[quote][1],
									 Assets[quote][1])
				amount_base = round(int(lo['sell_price']['base']['amount']) / 10 ** Assets[base][1], Assets[base][1])
			except Exception as err:
				print(err.__repr__())
			if Assets[base][0] in base_coins:  # buy
				price = round(amount_base / amount_quote, Assets[base][1])
				total = round(amount_quote * price, Assets[base][1])
				print("buy", Assets[quote][0], amount_quote, Assets[base][0], amount_base, price, date)
				#           0       1               2                   3           4       5       6       7       8               9           10
				ob[account[0]].append(["buy", Assets[quote][0], amount_quote, Assets[base][0], amount_base, price, total, date,
									   Assets[quote][1], Assets[base][1], lo['id']])
			else:
				price = round(amount_quote / amount_base, Assets[base][1])
				total = round(amount_base * price, Assets[base][1])
				print("sell", Assets[base][0], amount_base, Assets[quote][0], amount_quote, price, date)
				ob[account[0]].append(["sell", Assets[base][0], amount_base, Assets[quote][0], amount_quote, price, total, date,
									   Assets[base][1], Assets[quote][1], lo['id']])

	# Open positions are part of balance
	if Redisdb.get("balances_openpos") is None or True:
		opos2 = {}
		for acc in ob:
			opos2[acc] = {}
			opos = [[x[1], x[2]] for x in ob[acc] if x[0] == 'sell']
			opos.extend([[x[3], x[4]] for x in ob[acc] if x[0] == 'buy'])
			opos.sort(key=lambda x: x[0])
			asset = ''
			tot = 0
			for o in opos:
				if asset != o[0] and asset != '':
					opos2[acc][asset] = tot
					asset, tot = o[0], o[1]
				else:
					tot += o[1]
					if asset == '':
						asset = o[0]
			if tot > 0:
				opos2[acc][asset] = tot
			# store open pos balances with expiration
		Redisdb.setex("balances_openpos", 300, json.dumps(opos2))
	return ob


async def open_positions():
	global Assets
	alist = await account_list()
	if alist is None or len(alist) == 0:
		return None
	load_assets()

	ob = []
	for account in alist:
		try:
			account_data = Bitshares.rpc.get_full_accounts([account[0]], False)[0][1]
		except:
			continue
		# read call orders
		call_orders = []
		for co in account_data['call_orders']:
			quote = co['call_price']['quote']['asset_id']
			base = co['call_price']['base']['asset_id']
			try:
				amount_debt = round(int(co['debt']) / 10 ** Assets[quote][1], Assets[quote][1])
				amount_collateral = round(int(co['collateral']) / 10 ** Assets[base][1], Assets[base][1])
				call_orders.append([account[0], Assets[quote][0], amount_debt, Assets[base][0], amount_collateral])
			except Exception as err:
				print(err.__repr__())

		for lo in account_data['limit_orders']:
			quote = lo['sell_price']['quote']['asset_id']
			base = lo['sell_price']['base']['asset_id']
			pair = Assets_id[quote]+'/'+Assets_id[base]
			pair_inv = Assets_id[base]+'/'+Assets_id[quote]
			try:
				amount_quote = round(int(lo['sell_price']['quote']['amount']) / 10 ** Assets[quote][1],
									 Assets[quote][1])
				amount_base = round(int(lo['sell_price']['base']['amount']) / 10 ** Assets[base][1], Assets[base][1])
			except Exception as err:
				print(err.__repr__())
			# buy amount_quote quote for amount_base bases  (quote/base)
			# sell amount_base base for amount_quote quotes  (base/quote)
			price = round(amount_quote/amount_base, Assets[base][1])
			price_inv = round(amount_base/amount_quote, Assets[quote][1])

			ob.append([account[0], lo['id'], pair, 'buy', amount_quote, quote, amount_base, base, price, Assets[quote][1], Assets[base][1]])
			ob.append([account[0], lo['id'], pair_inv, 'sell', amount_base, base, amount_quote, quote, price_inv, Assets[base][1], Assets[quote][1]])
	Redisdb.setex("balances_openpos", 300, json.dumps(ob))
	# TODO: Open positions are part of balance
	return ob




def order_delete(id, conn, account):
	rtn = conn.cancel(id, account=account)
	Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'message': "Success"}))
