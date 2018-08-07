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
import hashlib
import base64
import pickle
import blockchain, accounts, ohlc_analysers, market_data
import passwordlock


WBTS = {}
Active_module = None
Assets_id = {}
Assets_name = {}
Ohlc_Analyser = None


def init():
	"""
	Initialisation
	*
	:return:
	"""
	import os
	global Assets_id, Assets_name
	os.chdir('../data')
	with open('assets.pickle', 'rb') as h:
		tmp = pickle.load(h)
	Assets_id = {k:v for (k,v) in [(k,v[0]) for (k,v) in tmp.items()]}
	Assets_name = {v:k for (k,v) in [(k,v[0]) for (k,v) in tmp.items()]}
	#TODO: is this need?
	#blockchain.init()
	Redisdb.bgsave()
	print("end")



def check_for_master_password():
	msg = None
	if Redisdb.get('master_hash') is None:
		msg = "Unlock with master password first."
	if msg is not None:
		Redisdb.rpush("datafeed", json.dumps({'module': "general", 'message': msg,'error': True}))
		return False
	return True





def privileged_connection(account_name):
	if not check_for_master_password():
		return
	if account_name not in WBTS or not WBTS[account_name].is_connected():
		tmp = accounts.account_list()
		wif = {x[0]: x[2] for x in tmp}
		WBTS[account_name] = BitShares(node=WSS_NODE, wif=wif[account_name])
	return WBTS[account_name]


class Operations_listener():

	def __init__(self):
		asyncio.get_event_loop().run_until_complete(self.do_operations())

	async def letmeuselocalcache(self, data):
		#TODO: prevent the use of cache if the settings have changed
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'], 'uselocalcache': False}))

	async def get_balances(self, data):
		# TODO: another column for asset collateral
		bal1, margin_lock_BTS, margin_lock_USD = await blockchain.get_balances()
		if bal1 is None:
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'message': "No account defined!", 'error': True}))
		else:
			Redisdb.rpush("datafeed", json.dumps({'module': data['module'], 'balances': bal1,
												'margin_lock_BTS': margin_lock_BTS,
												'margin_lock_USD': margin_lock_USD}))

	async def get_tradestats_token(self, data):
		stats = market_data.Stats()
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'],
							'stats_token': stats.stats_by_token[['asset_name', 'ops', 'volume', 'ops_day', 'volume_day']][:100].to_json(orient='values')}))

	async def get_tradestats_pair(self, data):
		stats = market_data.Stats()
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'],
							'stats_pair': stats.stats_by_pair[['pair_text', 'pair', 'pays_amount', 'receives_amount', 'price']][:200].to_json(orient='values')}))

	async def get_tradestats_account(self, data):
		stats = market_data.Stats()
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'],
							'stats_account': stats.stats_by_account[['account_id', 'pair']][:100].to_json(orient='values')}))

	async def get_tradestats_accountpair(self, data):
		stats = market_data.Stats()
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'],
							'stats_accountpair': stats.stats_by_account_pair[['account_id', 'pair_text', 'pair']][:100].to_json(orient='values')}))

	async def get_orderbook(self, data):
		buys = await blockchain.get_orderbook(data)
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'], 'orderbook': {'market': data['market'], 'date': arrow.utcnow().isoformat(), 'data': buys}}))


	async def open_positions(self, data):
		rtn = await blockchain.open_positions()
		Redisdb.rpush("datafeed", json.dumps({'module': data['module'], 'open_positions': rtn}))

	async def get_market_trades(self, data):
		movs = await blockchain.get_market_trades(data)
		if movs is not None and len(movs) > 0:
			movs.sort(key=lambda x: x[0])
			movs = movs[-100:]
			Redisdb.rpush("datafeed", json.dumps({'module': data['module'], 'market_trades': {'market': data['market'], 'data': movs}}))

	async def get_last_trades(self, data):
		global Ohlc_Analyser
		if Ohlc_Analyser is None:
			Ohlc_Analyser = ohlc_analysers.Analyze(range=(arrow.utcnow().shift(days=-7), arrow.utcnow()))
		a = Ohlc_Analyser
		tmp = data['market'].split('/')
		mkt = Assets_name[tmp[0]]+':'+Assets_name[tmp[1]]
		a.filter(pair=mkt)
		#a.filter()
		a.ohlc(timelapse="1h", fill=False)
		rdates = a.df_ohlc['time'].dt.to_pydatetime().tolist()
		rdates = [x.isoformat() for x in rdates]
		movs = [x for x in zip(rdates,
					 a.df_ohlc.price.open.tolist(), a.df_ohlc.price.close.tolist(),
					 a.df_ohlc.price.low.tolist(), a.df_ohlc.price.high.tolist(),
					 a.df_ohlc.receives_amount.receives_amount.tolist())]
		Redisdb.rpush("datafeed",
					  json.dumps({'module': Active_module, 'market_trades': {'market': data['market'], 'data': movs}}))

	async def account_list(self, dummy):
		accs = accounts.account_list()
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_account_list': accs}))

	async def account_new(self, data):
		accs = accounts.account_new(data)
		Redisdb.set("settings_accounts", json.dumps(accs))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_account_list': accs}))

	async def account_delete(self, data):
		accs = accounts.account_delete(data)
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'settings_account_list': accs}))
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "Account deleted"}))

	async def save_misc_settings(self, dat):
		rtn = Redisdb.get("settings_misc")
		if rtn is None:
			settings = {}
		else:
			settings = json.loads(rtn.decode('utf8'))
		for k in dat['data']:
			if k == "master_password":
				if dat['data'][k].lstrip() != '':
					passwordlock.store_mp(dat['data'][k])
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
		# need account 
		conn = privileged_connection(data['account'])
		if conn is None:
			return
		Redisdb.rpush("datafeed", json.dumps({'module': Active_module, 'message': "Order {0} delete?".format(data['id'])}))
		blockchain.order_delete(id=data['id'], conn=conn, account=data['account'])

	async def master_unlock(self, dat):
		if passwordlock.check_mp(dat['data']):
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'master_unlock': {'message': 'unlocked', 'error': False}}))
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'message': "Unlocked", 'error': False}))
			Redisdb.rpush("datafeed", json.dumps({'module': 'general', 'reload': 1}))
		else:
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

	async def rpc_ping(self):
		blockchain.read_ticker('BTS/CNY')


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
		# calls method
		print("calling:", dat['call'])
		fn = getattr(self, dat['call'], None)
		if fn is not None:
			await fn(dat)
		else:
			print("error: ", dat['call'], 'not defined')


	async def do_operations(self):

		while True:
			op = Redisdb.lpop("operations")
			if op is None:
				op = Redisdb.lpop("operations_bg")
				if op is None:
					await asyncio.sleep(.01)
					continue
			await self.do_ops(op)





if __name__ == "__main__":
	import sys
	# init is necesary the first run for load the assets
	if Redisdb.hget("asset1:BTS", 'symbol') is None:
		init()
	else:
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
