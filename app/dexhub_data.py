#
#
# (c) 2017 elias/vanissoft
#
# Bitshares comm
#
"""
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

Master_hash = None
Master_unlocked = False

WBTS = None
Active_module = None


def load_assets():
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


def init():
	"""
	Initialisation
	*
	:return:
	"""
	load_assets()
	Redisdb.bgsave()
	print("end")



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
	rtn = Redisdb.get("ticker_"+market)
	if rtn is not None:
		return json.loads(rtn.decode('utf8'))
	pair = market.split("/")
	# BTS/USD get ticker of BTS with prices in USD
	if pair[0] != pair[1]:
		rtn = Bitshares.rpc.get_ticker(pair[1], pair[0])
		mid_price = (float(rtn['lowest_ask']) + float(rtn['highest_bid']))/2
		chg_24h = float(rtn['percent_change'])
		volume = float(rtn['base_volume'])
		rtn = [mid_price, volume, chg_24h]
		Redisdb.setex("ticker_"+market, random.randint(200, 3000), json.dumps(rtn))
		return rtn
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
	bal = Redisdb.get('cache_balances')
	if bal is not None:
		bal = json.loads(bal.decode('utf8'))
		return bal

	alist = await account_list()
	if len(alist) == 0:
		return None

	while True:  # enable reenter due new assets
		bal = {}
		for account in alist:
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
					if symbol in bal:
						bal[symbol] = [bal[symbol][0] + amount, 0]
					else:
						bal[symbol] = [amount, 0]
		break
	Redisdb.setex("cache_balances", random.randint(200, 3000), json.dumps(bal))
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
		# read call orders
		if Redisdb.get("balances_callorders") is None:
			call_orders = []
			for co in account_data['call_orders']:
				quote = co['call_price']['quote']['asset_id']
				base = co['call_price']['base']['asset_id']
				quote_asset = [Redisdb.hget("asset2:"+quote, 'symbol').decode('utf8'), int(Redisdb.hget("asset2:"+quote, 'precision'))]
				base_asset =  [Redisdb.hget("asset2:"+base, 'symbol').decode('utf8'), int(Redisdb.hget("asset2:"+base, 'precision'))]
				try:
					amount_debt = round(int(co['debt']) / 10 ** quote_asset[1], quote_asset[1])
					amount_collateral = round(int(co['collateral']) / 10 ** base_asset[1], base_asset[1])
					call_orders.append([quote_asset[0], amount_debt, base_asset[0], amount_collateral])
				except Exception as err:
					print(err.__repr__())
			if len(call_orders) > 0:
				Redisdb.setex("balances_callorders", 300, json.dumps(call_orders))

		# {'top_n_control_flags': 0, 'statistics': '2.6.203202', 'id': '1.2.203202', 'membership_expiration_date': '1969-12-31T23:59:59', 'lifetime_referrer': '1.2.203202', 'lifetime_referrer_fee_percentage': 8000, 'blacklisting_accounts': [], 'options': {'num_committee': 3, 'extensions': [], 'votes': ['0:91', '0:147', '0:173', '2:194', '2:224', '2:231', '2:233'], 'voting_account': '1.2.266887', 'memo_key': 'BTS8QjksGCVaCKmZyspr7sraF77HDE7RQk44w8FgApcYQKtQUpwwT', 'num_witness': 0}, 'referrer_rewards_percentage': 0, 'name': 'tximiss0', 'active': {'weight_threshold': 1, 'key_auths': [['BTS8QjksGCVaCKmZyspr7sraF77HDE7RQk44w8FgApcYQKtQUpwwT', 1]], 'address_auths': [], 'account_auths': [['1.2.446518', 1]]}, 'referrer': '1.2.203202', 'owner_special_authority': [0, {}], 'whitelisting_accounts': [], 'network_fee_percentage': 2000, 'registrar': '1.2.203202', 'active_special_authority': [0, {}], 'owner': {'weight_threshold': 1, 'key_auths': [['BTS7QyUi34KRVmRR4wqTevosoz4BrKGMfR5HFVSmAW17DfUXkTYEK', 1]], 'address_auths': [], 'account_auths': []}, 'cashback_vb': '1.13.2164', 'blacklisted_accounts': [], 'whitelisted_accounts': []}
		base_coins = 'BTS,USD,CNY,RUB,EUR'.split(",")
		for lo in account_data['limit_orders']:
			quote =  lo['sell_price']['quote']['asset_id']
			base = lo['sell_price']['base']['asset_id']
			if Redisdb.hget("asset2:"+quote, 'symbol') is None:
				break
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
				#           0       1               2                   3           4       5       6       7       8               9           10
				ob.append(["buy", quote_asset[0], amount_quote, base_asset[0], amount_base, price, total, date, quote_asset[1], base_asset[1], lo['id']])
			else:
				price = round(amount_quote/amount_base, base_asset[1])
				total = round(amount_base*price, base_asset[1])
				print("sell", base_asset[0], amount_base, quote_asset[0], amount_quote, price, date)
				ob.append(["sell", base_asset[0], amount_base, quote_asset[0], amount_quote, price, total, date, base_asset[1], quote_asset[1], lo['id']])

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


def clear_cache():
	"""
	Clear cached data depending on accounts
	:return:
	"""
	Redisdb.delete("balances_openpos")
	Redisdb.delete("balances_callorders")


def check_for_master_password():
	msg = None
	if not Master_unlocked:
		msg = "Unlock with master password first."
	elif Master_hash is None:
		msg = "Setup a master password first and then unlock."
	if msg is not None:
		Redisdb.rpush("datafeed", json.dumps({'module': "general", 'message': msg,'error': True}))
		return False
	return True


def get_account_wif():
	if not Master_unlocked:
		return None
	rtn = Redisdb.get("settings_accounts")
	if rtn is None:
		accounts = []
	else:
		accounts = json.loads(rtn.decode('utf8'))
	cipher = Fernet(Master_hash)  # cipher with master key hash
	for ac in accounts:
		try:
			ac[2] = cipher.decrypt(ac[2].encode('utf8')).decode('utf8')
		except:
			ac[2] = "*error unlocking*"
	return accounts


class Operations_listener():

	def __init__(self):
		asyncio.get_event_loop().run_until_complete(self.do_operations())

	async def get_balances(self, dummy):
		# TODO: another column for asset collateral
		"""
		Return balance consolidated with "balances_openpos"
		:return: {'asset': [balance, open orders], ...}
		"""
		bal1 = await read_balances()
		if bal1 is None:
			Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "No account defined!", 'error': True}))
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
		base = await read_ticker("BTS/USD")
		#return [mid_price, volume, chg_24h]
		for b in bal1:
			tick = await read_ticker(b+"/BTS")
			for t in enumerate(tick):
				if t[1] == float('Infinity'):
					tick[t[0]] = 0
			bal1[b].append([tick[0]*base[0], tick[1]*base[0], tick[2], int(Redisdb.hget("asset1:" + b, 'precision'))])

		margin_lock_BTS = 0
		margin_lock_USD = 0
		bal3 = Redisdb.get("balances_callorders")
		if bal3 is not None:
			bal3 = json.loads(bal3.decode('utf8'))
			for b in bal3:
				tick = await read_ticker(b[0]+"/BTS")
				for t in enumerate(tick):
					if t[1] == float('Infinity'):
						tick[t[0]] = 0
				# assume that collateral is always BTS and value in USD (base)
				margin_lock_BTS += b[1]
				margin_lock_USD += (b[3] * base[0]) -  (b[1] * tick[0] * base[0])

		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'balances': bal1,
											'margin_lock_BTS': margin_lock_BTS,
											'margin_lock_USD': margin_lock_USD}))


	async def get_orderbook(self, data):
		mkt = data['market']
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

		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'orderbook': {'market': mkt, 'date': arrow.utcnow().isoformat(), 'data': buys}}))


	async def open_positions(self, dummy):
		rtn = await read_open_positions()
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'open_positions': rtn}))


	def normalize_isoformat(dat):
		if len(dat) < 32:
			part = dat.split("+")
			return part[0]+".000000+"+part[1]
		else:
			return dat


	async def get_market_trades(self, data):
		mkt, date_from, date_to = (data['market'], data['date_from'], data['date_to'])
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
			th = Bitshares.rpc.get_market_history(base, quote, 3600, date_init.isoformat(), date_end.isoformat(), api_id='history')
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
			Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'market_trades': {'market': mkt, 'data': movs}}))

	async def account_list(self, dummy):
		rtn = get_account_wif()
		if rtn is None:
			accounts = []
			rtn = Redisdb.get("settings_accounts")
			if rtn is None:
				accounts = []
			else:
				accounts = json.loads(rtn.decode('utf8'))
			for ac in accounts:
				ac[2] = "*unlock for view*"
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_account_list': accounts}))

	async def account_new(self, data):
		dat = data['data']
		rtn = Redisdb.get("settings_accounts")
		if rtn is None:
			accounts = []
		else:
			accounts = json.loads(rtn.decode('utf8'))
		tmp = Bitshares.rpc.get_account(dat[0])
		if tmp is None:
			Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "Account doesn't exists<br><strong>"+dat[0]+"</strong>", 'error': True}))
			return
		if not check_for_master_password():
			return
		account_id = tmp['id']
		dat.append(account_id)
		cipher = Fernet(Master_hash)  # cipher with master key hash
		dat[2] = cipher.encrypt(dat[2].encode('utf8')).decode()
		accounts.append(dat)
		clear_cache()
		Redisdb.set("settings_accounts", json.dumps(accounts))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_account_list': accounts}))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "Account created<br><strong>"+dat[0]+"</strong>"}))

	async def account_delete(self, data):
		id = data['id']
		rtn = Redisdb.get("settings_accounts")
		if rtn is None:
			accounts = []
		else:
			accounts = json.loads(rtn.decode('utf8'))
			accounts.pop(id)
			Redisdb.set("settings_accounts", json.dumps(accounts))
		clear_cache()
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_account_list': accounts}))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "Account deleted"}))

	async def save_misc_settings(self, dat):
		global Master_hash
		rtn = Redisdb.get("settings_misc")
		if rtn is None:
			settings = {}
		else:
			settings = json.loads(rtn.decode('utf8'))
		for k in dat['data']:
			if k == "master_password":
				if dat['data'][k].lstrip() != '':
					Master_hash = base64.urlsafe_b64encode(hashlib.sha256(bytes(str(dat['data'][k]), 'utf8')).digest()).decode('utf8')
					settings[k] = Master_hash
			else:
				settings[k] = dat['data'][k]
		Redisdb.set("settings_misc", json.dumps(settings))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_misc': settings}))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "settings saved"}))

	async def get_settings_misc(self, dummy):
		rtn = Redisdb.get("settings_misc")
		if rtn is None:
			settings = {}
		else:
			settings = json.loads(rtn.decode('utf8'))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_misc': settings}))

	async def order_delete(self, data):
		id = data['id']
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "Order {0} delete?".format(id)}))

	async def master_unlock(self, dat):
		global Master_unlocked, WBTS
		if base64.urlsafe_b64encode(hashlib.sha256(bytes(str(dat['data']), 'utf8')).digest()).decode('utf8') == Master_hash:
			Master_unlocked = True
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'master_unlock': {'message': 'unlocked', 'error': False}}))
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'message': "Unlocked", 'error': False}))
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'reload': 1}))
			#WBTS = BitShares(node="wss://bitshares.openledger.info/ws", wif=dat['form']['key'])
		else:
			Master_unlocked = False
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'master_unlock': {'message': "password does not match", 'error': True}}))
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'message': "Password does not match", 'error': True}))

	async def marketpanels_savelayout(self, dat):
		Redisdb.set("MarketPanels_layout", dat['data'])

	async def marketpanels_loadlayout(self, dat):
		default = [["OPEN.ETH/BTS", 1]]
		rtn = Redisdb.get("MarketPanels_layout")
		if rtn is None:
			layout = default
		else:
			layout = json.loads(rtn.decode('utf8'))
			if len(layout) == 0:
				layout = default
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'marketpanels_layout': layout}))

	async def ping(self):
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'data': 'pong'}))


	async def do_ops(self, op):
		"""
		Process the enqueued operations.
		:param op:
		:return:
		"""
		# TODO: as this module is a worker it is a must getting global settings
		global Active_module
		Active_module = Redisdb.get('Active_module').decode('utf8')

		try:
			dat = json.loads(op.decode('utf8'))
		except Exception as err:
			print(err.__repr__())
			return
		if dat['module'] != 'general' and dat['module'] != Redisdb.get('Active_module').decode('utf8'):  # discard
			print("discard", dat['module'], Redisdb.get('Active_module').decode('utf8'))
			return
		# calls method
		fn = getattr(self, dat['call'], None)
		if fn is not None:
			await fn(dat)
		else:
			print("error: ", dat['call'], 'not defined')


	async def do_operations(self):
		global Master_hash
		rtn = Redisdb.get("settings_misc")
		if rtn is not None:
			Master_hash = json.loads(rtn.decode('utf8'))['master_password']

		while True:
			op = Redisdb.lpop("operations")
			if op is None:
				op = Redisdb.lpop("operations_bg")
				await asyncio.sleep(.01)
				if op is None:
					continue
			await self.do_ops(op)





if __name__ == "__main__":
	import sys
	# init is necesary the first run for load the assets
	if Redisdb.hget("asset1:BTS", 'symbol') is None:
		init()
	if len(sys.argv) > 1:
		if 'init' in sys.argv[1]:
			init()
		elif 'blockchain_listener' in sys.argv[1]:
			blockchain_listener()
		elif 'operations_listener' in sys.argv[1]:
			Operations_listener()
	else:
		# runs in bg, invoked in main
		Operations_listener()
