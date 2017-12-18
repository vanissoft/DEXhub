#
# (c) 2017 elias/vanissoft
#
#

BTS_ACCOUNT = "XXXXX"
BTS_ACCOUNT_ID = None

PORT = 8808
REDIS_PORT = 6386
WSS_NODE = "wss://bitshares.openledger.info/ws"

import redis

Redisdb = redis.StrictRedis(host='127.0.0.1', port=REDIS_PORT, db=0)

from bitshares import BitShares
Bitshares = BitShares(WSS_NODE)
BTS_ACCOUNT_ID = Bitshares.rpc.get_account(BTS_ACCOUNT)['id']
