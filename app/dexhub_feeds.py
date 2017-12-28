#
# (c) 2017 elias/vanissoft
#
# Bitshares feeds
#
"""

	Feeds:
		Coinmarketcap
		Bittrex
		Poloniex


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
		if dat['what'] == 'orderbook':
			await get_orderbook(dat['market'])
		elif dat['what'] == 'open_positions':
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
