#
# (c) 2017 elias/vanissoft
#
#

PORT = 8808
REDIS_PORT = 6386
WSS_NODE = "wss://eu.nodes.bitshares.ws"
WORKERS = 2

import redis

Redisdb = redis.StrictRedis(host='127.0.0.1', port=REDIS_PORT, db=0)

from bitshares import BitShares
Bitshares = BitShares(WSS_NODE)
