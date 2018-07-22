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


def init():
	"""
	Loads initial data from Bitshares Blockchain
	*
	:return:
	"""
	# TODO: obtain the last block number
	# TODO: retrieve account history
	# TODO: load balances
	# TODO: load open positions

	from bitshares import account

	async def load_assets():
		"""
		Load all the Bitshares assets.
		:return:
		"""
		print("bitshares_data.init > load_assets")
		def write(batch):
			"""
			Writes assets to DB
			:param batch:
			:return:
			"""
			p = Redisdb.pipeline()
			for b in batch:
				for k in b.keys():
					if k == 'options':
						p.hset("asset1:" + b['symbol'], k, json.dumps(b[k]))
						p.hset("asset2:" + b['id'], k, json.dumps(b[k]))
					else:
						p.hset("asset1:" + b['symbol'], k, b[k])
						p.hset("asset2:" + b['id'], k, b[k])
			p.incr("status:loading_assets", 100)
			p.execute()

		Redisdb.set("status:loading_assets", 0)
		cols = "id,issuer,dynamic_asset_data_id,symbol,precision,description_main,description_market,\
				description_short_name,market_fee_percent,issuer_permissions,flags,max_supply,options".split(",")
		next_asset = ""
		while True:
			dassets = []
			assets = Bitshares.rpc.list_assets(next_asset, 100)
			for a in assets:
				row = {}
				for col in a.keys():
					if col in cols:
						row[col] = a[col]
				for col in a['options'].keys():
					if col in cols:
						row[col] = a['options'][col]
				row['description_main'] = ''
				row['description_market'] = ''
				row['description_short_name'] = ''
				if a['options']['description'][:1] == "{":
					desc = json.loads(a['options']['description'])
					row['description_main'] = desc['main']
					if 'market' in desc:
						row['description_market'] = desc['market']
					if 'short_name' in desc:
						row['description_short_name'] = desc['short_name']
				else:
					row['description_main'] = a['options']['description']
				dassets.append(row)
			write(dassets)
			next_asset = a['symbol'] + " "
			if len(assets) < 100:
				break
		Redisdb.set("status:loading_assets", len(assets))
		print("bitshares_data.init > load_assets end")


	tasks = [asyncio.ensure_future(load_assets())]

	loop = asyncio.get_event_loop()
	loop.run_until_complete(asyncio.wait(tasks))

	Redisdb.bgsave()
	print("end")



# TODO: dismissed in favour of limit_orders
def datatables():
	"""
	Return data relevant to datatables module.
	:return:
	"""
	try:
		opos = json.loads(Redisdb.get('open_positions').decode('utf8'))
	except Exception as err:
		opos = None
		print(err.__repr__())
	rtn = {'open_positions': opos}
	return rtn


def limitorders():
	"""
	Return data relevant to limitorders module.
	At starts
	:return:
	"""
	return None



def dashboard():
	return []








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


async def read_ticker(market):
	# TODO: make lazy execution
	pair = market.split("/")
	# BTS/USD get ticker of BTS with prices in USD
	if pair[0] != pair[1]:
		rtn = Bitshares.rpc.get_ticker(pair[1], pair[0])
		mid_price = (float(rtn['lowest_ask']) + float(rtn['highest_bid']))/2
		chg_24h = float(rtn['percent_change'])
		volume = float(rtn['base_volume'])
		return [mid_price, volume, chg_24h]
	else:
		return [1,0,0]

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
	bal = {}
	for account in alist:
		try:
			rtn = Bitshares.rpc.get_account_balances(account[3], [])
		except Exception as err:
			rtn = []
			print(err.__repr__())
		for r in rtn:
			prec = int(Redisdb.hget("asset2:" + r['asset_id'], 'precision'))
			symbol = Redisdb.hget("asset2:" + r['asset_id'], 'symbol').decode('utf8')
			amount = round(int(r['amount']) / 10 ** prec, prec)
			if amount > 0:
				if symbol in bal:
					bal[symbol] = [bal[symbol][0] + amount, 0]
				else:
					bal[symbol] = [amount, 0]
	return bal


async def read_open_positions():
	alist = await account_list()
	if len(alist) == 0:
		return None

	ob = []
	for account in alist:
		try:
			account_data = Bitshares.rpc.get_full_accounts([account[0]], False)[0][1]
		except:
			continue
		# {'top_n_control_flags': 0, 'statistics': '2.6.203202', 'id': '1.2.203202', 'membership_expiration_date': '1969-12-31T23:59:59', 'lifetime_referrer': '1.2.203202', 'lifetime_referrer_fee_percentage': 8000, 'blacklisting_accounts': [], 'options': {'num_committee': 3, 'extensions': [], 'votes': ['0:91', '0:147', '0:173', '2:194', '2:224', '2:231', '2:233'], 'voting_account': '1.2.266887', 'memo_key': 'BTS8QjksGCVaCKmZyspr7sraF77HDE7RQk44w8FgApcYQKtQUpwwT', 'num_witness': 0}, 'referrer_rewards_percentage': 0, 'name': 'tximiss0', 'active': {'weight_threshold': 1, 'key_auths': [['BTS8QjksGCVaCKmZyspr7sraF77HDE7RQk44w8FgApcYQKtQUpwwT', 1]], 'address_auths': [], 'account_auths': [['1.2.446518', 1]]}, 'referrer': '1.2.203202', 'owner_special_authority': [0, {}], 'whitelisting_accounts': [], 'network_fee_percentage': 2000, 'registrar': '1.2.203202', 'active_special_authority': [0, {}], 'owner': {'weight_threshold': 1, 'key_auths': [['BTS7QyUi34KRVmRR4wqTevosoz4BrKGMfR5HFVSmAW17DfUXkTYEK', 1]], 'address_auths': [], 'account_auths': []}, 'cashback_vb': '1.13.2164', 'blacklisted_accounts': [], 'whitelisted_accounts': []}
		limit_orders = account_data['limit_orders']
		base_coins = 'BTS,USD,CNY,RUB,EUR'.split(",")
		for lo in limit_orders:
			quote =  lo['sell_price']['quote']['asset_id']
			base = lo['sell_price']['base']['asset_id']
			quote_asset = [Redisdb.hget("asset2:"+quote, 'symbol').decode('utf8'), int(Redisdb.hget("asset2:"+quote, 'precision'))]
			base_asset =  [Redisdb.hget("asset2:"+base, 'symbol').decode('utf8'), int(Redisdb.hget("asset2:"+base, 'precision'))]
			date = arrow.get(lo['expiration']).shift(years=-5).isoformat()
			try:
				amount_quote = round(int(lo['sell_price']['quote']['amount']) / 10 ** quote_asset[1], quote_asset[1])
				amount_base = round(int(lo['sell_price']['base']['amount']) / 10 ** base_asset[1], base_asset[1])
			except Exception as err:
				print(err.__repr__())
			if base_asset[0] in base_coins:  # buy
				price = round(amount_base/amount_quote, base_asset[1])
				total = round(amount_quote*price, base_asset[1])
				print("buy", quote_asset[0], amount_quote, base_asset[0], amount_base, price, date)
				ob.append(["buy", quote_asset[0], amount_quote, base_asset[0], amount_base, price, total, date, quote_asset[1], base_asset[1]])
			else:
				price = round(amount_quote/amount_base, base_asset[1])
				total = round(amount_base*price, base_asset[1])
				print("sell", base_asset[0], amount_base, quote_asset[0], amount_quote, price, date)
				ob.append(["sell", base_asset[0], amount_base, quote_asset[0], amount_quote, price, total, date, base_asset[1], quote_asset[1]])

	# Open positions are part of balance
	if Redisdb.get("balances_openpos") is None:
		opos = [[x[1], x[2]] for x in ob if x[0]=='sell']
		opos.extend([[x[3], x[4]] for x in ob if x[0]=='buy'])
		opos.sort(key=lambda x: x[0])
		opos2 = {}
		asset = ''
		tot = 0
		for o in opos:
			if asset != o[0] and asset != '':
				opos2[asset] = tot
				asset, tot = o[0], o[1]
			else:
				tot += o[1]
				if asset == '':
					asset = o[0]
		if tot > 0:
			opos2[asset] = tot
		# store open pos balances with expiration
		Redisdb.setex("balances_openpos", 300, json.dumps(opos2))
	return ob




def operations_listener():

	async def get_balances():
		"""
		Return balance consolidated with "balances_openpos"
		:return: {'asset': [balance, open orders], ...}
		"""
		bal1 = await read_balances()
		if bal1 is None:
			Redisdb.rpush("datafeed", json.dumps({'message': "No account defined!", 'error': True}))
			return
		bal2 = Redisdb.get("balances_openpos")
		if bal2 is None:
			rtn = await read_open_positions()
			bal2 = Redisdb.get("balances_openpos")
		bal2 = json.loads(bal2.decode('utf8'))
		for b in bal2:
			if b in bal1:
				bal1[b] = [bal1[b][0], bal2[b]]
			else:
				bal1[b] = [0, bal2[b]]
		# TODO: defer execution and send in another packet
		base = await read_ticker("BTS/USD")
		#return [mid_price, volume, chg_24h]
		for b in bal1:
			tick = await read_ticker(b+"/BTS")
			bal1[b].append([tick[0]*base[0], tick[1]*base[0], tick[2]])
		Redisdb.rpush("datafeed", json.dumps({'balances': bal1}))


	async def get_orderbook(mkt):
		pairs = mkt.split("/")
		p1 = Redisdb.hget("asset1:" + pairs[0], 'id').decode('utf8')
		p1_prec = int(Redisdb.hget("asset1:" + pairs[0], 'precision'))
		p2 = Redisdb.hget("asset1:" + pairs[1], 'id').decode('utf8')
		p2_prec = int(Redisdb.hget("asset1:" + pairs[1], 'precision'))
		rtn = Bitshares.rpc.get_limit_orders(p1, p2, 5000)

		dat = []
		for pos in rtn:
			if p1 == pos['sell_price']['quote']['asset_id']:  # buy
				amount_base = int(pos['sell_price']['base']['amount']) / 10 ** p2_prec
				amount_quote = int(pos['sell_price']['quote']['amount']) / 10 ** p1_prec
				price = round(amount_base / amount_quote, p2_prec)
				total = round(amount_quote * price, p2_prec)
				op = 'buy'
			else:  # sell
				amount_base = int(pos['sell_price']['base']['amount']) / 10 ** p1_prec
				amount_quote = int(pos['sell_price']['quote']['amount']) / 10 ** p2_prec
				price = round(amount_quote / amount_base, p2_prec)
				total = round(amount_base*price, p2_prec)
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

		Redisdb.rpush("datafeed", json.dumps({'orderbook': {'market': mkt, 'date': arrow.utcnow().isoformat(), 'data': buys}}))


	async def get_open_positions():
		rtn = await read_open_positions()
		Redisdb.rpush("datafeed", json.dumps({'open_positions': rtn}))


	def normalize_isoformat(dat):
		if len(dat) < 32:
			part = dat.split("+")
			return part[0]+".000000+"+part[1]
		else:
			return dat


	async def get_market_trades(mkt, date_from, date_to):
		pairs = mkt.split("/")
		quote = Redisdb.hget("asset1:" + pairs[0], 'id').decode('utf8')  # quote
		quote_prec = int(Redisdb.hget("asset1:" + pairs[0], 'precision'))
		base = Redisdb.hget("asset1:" + pairs[1], 'id').decode('utf8')  # base
		base_prec = int(Redisdb.hget("asset1:" + pairs[1], 'precision'))

		date_end = arrow.utcnow()
		date_init = date_end.shift(months=-1)
		print(mkt, date_init, date_end)
		movs = []
		while True:
			th = Bitshares.rpc.get_market_history(base, quote, 3600, date_init.isoformat(), date_end.isoformat(), api_id=3)
			if len(th) == 0:
				return
			th.sort(key=lambda x: x['key']['open'])
			for t in th:
				dat = {}
				try:
					dat['open'] = round(
						(float(t['open_base']) / 10 ** base_prec) / (float(t['open_quote']) / 10 ** quote_prec),
						base_prec)
					if t['close_quote'] == 0:
						dat['close'] = dat['open']
					else:
						dat['close'] = round((float(t['close_base']) / 10 ** base_prec) / (float(t['close_quote']) / 10 ** quote_prec), base_prec)
					if t['high_quote'] == 0:
						if dat['open'] > dat['close']:
							dat['high'] = dat['open']
						else:
							dat['high'] = dat['close']
					else:
						dat['high'] = round((float(t['high_base'])/10**base_prec) / (float(t['high_quote'])/10**quote_prec), base_prec)
					if t['low_quote'] == 1:
						if dat['open'] < dat['close']:
							dat['low'] = dat['open']
						else:
							dat['low'] = dat['close']
					else:
						dat['low'] = round((float(t['low_base'])/10**base_prec) / (float(t['low_quote'])/10**quote_prec), base_prec)
					dat['volume'] = round(float(t['base_volume'])/10**base_prec, base_prec)
					dat['date'] = t['key']['open']
					movs.append([dat['date'], dat['open'], dat['close'], dat['low'], dat['high'], dat['volume']])
				except Exception as err:
					print("error", err.__repr__())
					print(t['high_base'], t['high_quote'], t['low_base'], t['low_quote'])
					continue
			if len(th) < 200:
				break
			date_init = arrow.get(th[-1]['key']['open']).shift(seconds=+0.01)
			print("  ", date_init, date_end)

		if len(movs) > 0:
			movs.sort(key=lambda x: x[0])
			movs = movs[-100:]
			movs2 = [["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
				["2004-01-05", 10411.85, 10544.07, 10411.85, 10575.92, 221290000],
				["2004-01-06", 10543.85, 10538.66, 10454.37, 10584.07, 191460000],
				["2004-01-07", 10535.46, 10529.03, 10432, 10587.55, 225490000],
				["2004-04-20", 10437.85, 10314.5, 10297.39, 10530.61, 204710000],
				["2004-04-21", 10311.87, 10317.27, 10200.38, 10398.53, 232630000],
				["2004-04-22", 10314.99, 10461.2, 10255.88, 10529.12, 265740000]]
			#movs.sort(key=lambda x: x[0])
			Redisdb.rpush("datafeed", json.dumps({'market_trades': {'market': mkt, 'data': movs}}))

	async def get_settings_account_list():
		rtn = Redisdb.get("settings_accounts")
		if rtn is None:
			accounts = []
		else:
			accounts = json.loads(rtn.decode('utf8'))
		Redisdb.rpush("datafeed", json.dumps({'settings_account_list': accounts}))

	async def settings_account_new(dat):
		rtn = Redisdb.get("settings_accounts")
		if rtn is None:
			accounts = []
		else:
			accounts = json.loads(rtn.decode('utf8'))
		account_id = Bitshares.rpc.get_account(dat[0])['id']
		dat.append(account_id)
		accounts.append(dat)
		Redisdb.set("settings_accounts", json.dumps(accounts))
		Redisdb.rpush("datafeed", json.dumps({'settings_account_list': accounts}))
		Redisdb.rpush("datafeed", json.dumps({'message': "Account created<br><strong>"+dat[0]+"</strong>"}))

	async def settings_account_del(id):
		rtn = Redisdb.get("settings_accounts")
		if rtn is None:
			accounts = []
		else:
			accounts = json.loads(rtn.decode('utf8'))
			accounts.pop(id)
			Redisdb.set("settings_accounts", json.dumps(accounts))
		Redisdb.rpush("datafeed", json.dumps({'settings_account_list': accounts}))
		Redisdb.rpush("datafeed", json.dumps({'message': "Account deleted"}))

	async def settings_misc_save(dat):
		rtn = Redisdb.get("settings_misc")
		if rtn is None:
			settings = {}
		else:
			settings = json.loads(rtn.decode('utf8'))
		for k in dat['data']:
			settings[k] = dat['data'][k]
		Redisdb.set("settings_misc", json.dumps(settings))
		Redisdb.rpush("datafeed", json.dumps({'settings_misc': settings}))
		Redisdb.rpush("datafeed", json.dumps({'message': "settings saved"}))

	async def get_settings_misc():
		rtn = Redisdb.get("settings_misc")
		if rtn is None:
			settings = {}
		else:
			settings = json.loads(rtn.decode('utf8'))
		Redisdb.rpush("datafeed", json.dumps({'settings_misc': settings}))

	async def master_unlock(dat):
		rtn = Redisdb.get("settings_misc")
		if rtn is None:
			return False
		settings = json.loads(rtn.decode('utf8'))
		if dat['data'] == settings['master_password']:
			Redisdb.rpush("datafeed", json.dumps({'master_unlock': {'message': 'unlocked', 'error': False}}))
			Redisdb.rpush("datafeed", json.dumps({'message': "Unlocked", 'error': False}))
		else:
			Redisdb.rpush("datafeed", json.dumps({'master_unlock': {'message': "password does not match", 'error': True}}))
			Redisdb.rpush("datafeed", json.dumps({'message': "Password does not match", 'error': True}))


	async def do_ops(op):
		"""
		Process the enqueued operations.
		:param op:
		:return:
		"""
		try:
			dat = json.loads(op.decode('utf8'))
		except Exception as err:
			print(err.__repr__())
			return
		if dat['call'] == 'orderbook':
			await get_orderbook(dat['market'])
		elif dat['call'] == 'open_positions':
			await get_open_positions()
		elif dat['call'] == 'get_market_trades':
			await get_market_trades(dat['market'], dat['date_from'], dat['date_to'])
		elif dat['call'] == 'get_balances':
			await get_balances()
		elif dat['call'] == 'account_list':
			await get_settings_account_list()
		elif dat['call'] == 'new_account':
			await settings_account_new(dat['data'])
		elif dat['call'] == 'del_account':
			await settings_account_del(dat['id'])
		elif dat['call'] == 'save_misc_settings':
			await settings_misc_save(dat)
		elif dat['call'] == 'get_settings_misc':
			await get_settings_misc()
		elif dat['call'] == 'master_unlock':
			await master_unlock(dat)


	async def do_operations():
		while True:
			op = Redisdb.lpop("operations")
			if op is None:
				op = Redisdb.lpop("operations_bg")
				await asyncio.sleep(.01)
				if op is None:
					continue
			await do_ops(op)


	asyncio.get_event_loop().run_until_complete(do_operations())



if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		if 'init' in sys.argv[1]:
			init()
		elif 'blockchain_listener' in sys.argv[1]:
			blockchain_listener()
		elif 'operations_listener' in sys.argv[1]:
			operations_listener()
	else:
		# init is necesary the first run for load the assets
		#init()

		# runs in bg, invoked in main
		operations_listener()
