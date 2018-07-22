#
# (c) 2017 elias/vanissoft
#
# Bitshares feeds
#
"""

	Feeds:
		Coinmarketcap
		Bittrex ?
		Poloniex ?


	Store of data:
		????
		Redisdb.set("open_positions", json.dumps(ob))
		hset("market_history:BRIDE/BTS", "2017-11-27", "123123.232@232.23")
		Redisdb.set("settings_accounts", json.dumps(accounts))
		"balances"

	Bus:
		Redisdb.rpush("datafeed", json.dumps({'feeds': {'market': mkt, 'date': arrow.utcnow().isoformat(), 'type': x}}))

"""




import asyncio
import json
import arrow


# TODO: placed here for future reference
def load_coinmarketcap(curr):
	"""
	For each currency load capitalisation data from CoinMarketCap
	:param curr:
	:return:
	"""
	print("***", "load_coinmarketcap", curr)
	cu = db1.b_currencies
	cm = db1.cmc_datapoints
	cmkt = db1.b_coinmarketcap
	#url = 'http://graphs.coinmarketcap.com/v1/datapoints/'
	url = 'https://graphs.coinmarketcap.com/currencies/'
	rs2 = cm.select().order_by(cm.Date.desc()).where(cm.Coin == curr).limit(1).execute()
	to_date = datetime.today().timestamp()
	if rs2.count == 0:
		from_date = datetime(year=2004, month=1, day=1).timestamp()
	else:
		from_date = [r2._data['Date'] for r2 in rs2][0].timestamp() + 1
	rs3 = cu.select().where(cu.Currency == curr).execute()
	if rs3.count == 0:
		return False
	tmp3 = [r3._data for r3 in rs3][0]
	coin = tmp3['CoinMarketCap_Name']
	if coin is None:
		coin = tmp3['CurrencyLong'].replace(' ', '-')
	url2 = url + coin + '/' + str(int(from_date)) + '000'
	url2 += '/' + str(int(to_date)) + '000'
	hdrs = {'Host': 'graphs.coinmarketcap.com', 'Upgrade-Insecure-Requests': 1,
		'User-Agent': 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/56.0.2924.76 Chrome/56.0.2924.76 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Encoding': 'gzip,deflate,sdch', 'Accept-Language': 'en-US,en;q=0.8'}
	rtn = requests.get(url2, headers=hdrs)
	time.sleep(6)
	if rtn.status_code != 200:
		time.sleep(1)
		print("error ", coin, url2, rtn.reason, rtn.content)
		return False
	try:
		rst = json.loads(rtn.content.decode('utf-8'))
	except:
		print("coinmarketcap error decoding", url2, coin)
		time.sleep(1)
		return False
	ri = []
	coin2 = coin.split("/")[1] if ('/' in coin) else coin
	try:
		print(">", coin2)
		rtn2 = requests.get('http://api.coinmarketcap.com/v1/ticker/'+coin2+'/', headers=hdrs)
		rst2 = json.loads(rtn2.content.decode('utf-8'))[0]
		tmp = [None, None]
		tmp[0] = int(float(rst2['available_supply'])) if rst2['available_supply'] is not None else None
		tmp[1] = int(float(rst2['total_supply'])) if rst2['total_supply'] is not None else None
		icurr = {'AvailableSupply': tmp[0], 'TotalSupply': tmp[1],
					'TimeStamp': datetime.today(), 'Currency': curr}
		cmkt.insert(**icurr).execute()
	except:
		print("coinmarketcap tiker error ", 'http://api.coinmarketcap.com/v1/ticker/'+coin2+'/')

	for n in range(0, len(rst['price_usd'])):
		ri.append({'Coin': curr, 'Date': datetime.fromtimestamp(float(str(rst['price_usd'][n][0])[:-3])),
			'PriceBtc': rst['price_btc'][n][1], 'PriceUsd': rst['price_usd'][n][1],
			'VolumeUsd': rst['volume_usd'][n][1], 'MarketCapBy': rst['market_cap_by_available_supply'][n][1]})
	if len(rst['price_usd']) > 0:
		cm.insert_many(ri).execute()
		return True
	else:
		return False




def feed_listener():

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

	async def do_operations():
		while True:
			op = Redisdb.lpop("feed_read")
			if op is None:
				await asyncio.sleep(.01)
				continue
			await do_ops(op)

	asyncio.get_event_loop().run_until_complete(do_operations())

if __name__ == "__main__":
	feed_listener()
