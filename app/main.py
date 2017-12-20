#
#
# (c) 2017 elias/vanissoft
#
#



import subprocess
import time
import socket  # only for debug conmuting

from asyncio import sleep
from sanic import Sanic
from sanic_compress import Compress
from sanic.response import json as response_json, text as response_text, html as response_html, file as response_file
from sanic.exceptions import ServerError

import json
import random

from render import Render
import mreq
import bitshares_data
import data_store

Client_comm = None
Active_modname = None
Procs = []
Develop = False


# ----------- CONSTANTS
from config import *

app = Sanic()
app.config['COMPRESS_MIMETYPES'] = ('text/x-python', 'application/javascript', 'text/css', 'text/html', 'text/plain')
Compress(app)

@app.middleware('request')
async def req1(req):
	print("req1", req.url)
	if '/get/' in req.path or '/do/' in req.path or '/post/' in req.path or '/comm' in req.path:
		return None
	path = req.path.split("&")[0]
	ext = path.split('.')[-1]
	if ext in ('mp3', 'js', 'jpg', 'css', 'ttf', 'png', 'woff', 'woff2', 'ico', 'gif', 'map', 'mem', 'pck', 'mp4', 'csv'):
		pfil = './web' + path
		return await response_file(location=pfil, headers={"cache-control": "public,max-age=216000"})
	elif ext in 'html':
		pfil = './web' + path
		tmp = Render(pfil)
		rtn = await tmp.parse()
		return response_html(body=rtn, headers={"cache-control": "public,max-age=216000"})
	elif ext in 'py':
		pfil = '.' + path
		# /w*.py y /vs_widgets will be served not server side .py
		if (path[:2] == '/w' or "/vs_widgets" in path) and ".." not in path:
			return await response_file(pfil, headers={"cache-control": "public,max-age=0"})
		else:
			return response_text("error")
	else:
		return response_text("error")


@app.route('/<tag>')
async def route1(req, tag):
	return response_text(tag)


@app.route('/get/<tag>', methods=['GET'])
async def getinfo(req, tag):
	rtn = mreq.getinfo(req.args, tag, req.path, req.query_string)
	return response_json(rtn)


@app.route('/post/<tag>', methods=['POST'])
async def postinfo(req, tag):
	rtn = mreq.postinfo(req.args, tag, req.path, req.query_string, req.json)
	return response_text(rtn)



@app.websocket('/comm')
async def wscomms(request, ws):
	global Client_comm, Active_modname
	while True:
		data = await ws.recv()
		if data is not None:
			Client_comm = ws
			print('1Received from client: ' + data)
			try:
				dat = json.loads(data)
				if 'operation' in dat:
					if dat['operation'] == 'module_activation':
						Redisdb.bgsave()
						Redisdb.delete('operations')  # cleanup
						Redisdb.rpush('operations', json.dumps({'what': 'data_store_save'}))
						Active_modname = dat['module']
						# initial data?
						#rtn = getattr(bitshares_data, Active_modname)()
						#await ws.send(json.dumps({"data": rtn}))

					elif dat['operation'] == 'enqueue':
						del dat['operation']
						Redisdb.rpush('operations', json.dumps(dat))

					elif dat['operation'] == 'enqueue_bg':
						del dat['operation']
						Redisdb.rpush('operations_bg', json.dumps(dat))

			except Exception as err:
				print('2Received from client: ', err.__repr__())



def dummy(param):
	print(param)


async def feeder():
	global Active_modname
	while True:
		if Client_comm is not None:
			if Active_modname == 'dashboard':
				await Client_comm.send(json.dumps({'module': 'dashboard', 'data': random.random()}))
				await sleep(2)
		while True:
			# TODO: loop until the datafeed queue gets empty
			rtn = Redisdb.lpop("datafeed")
			if rtn is None:
				break
			df = json.loads(rtn.decode('utf8'))
			dat = {'module': Active_modname, 'data': df}
			try:
				await Client_comm.send(json.dumps(dat))
			except Exception as err:
				print(err.__repr__())
		await sleep(0.01)


async def broker():
	while True:
		while True:
			if Client_comm is not None:
				print("sending")
				await Client_comm.send("from the server")

			rtn = Redisdb.lpop("operations")
			if rtn is None:
				break
			op = pickle.loads(rtn)
			if op['operation'] == 'launch_distribution':
				distribution.enqueue(op, Q_bg)
			elif op['operation'] == 'distribution_batch':
				distribution.batch_enqueue(op, Q_bg)
		await sleep(1)



if __name__ == '__main__':
	# Develop switch conmute between queue and direct work. True for be able to put Breakpoints
	Develop = ('Z68X' in socket.getfqdn()) and True
	proc1 = subprocess.Popen("redis-server --port "+str(REDIS_PORT), shell=True)
	while True:
		try:
			Redisdb = redis.StrictRedis(host='127.0.0.1', port=REDIS_PORT, db=0)
			# cleanup
			Redisdb.delete('messages')
			Redisdb.delete('operations')
			Redisdb.delete("batch_jobs")
			break
		except:
			time.sleep(1)

	proc2 = []

	# initial load of assets
	#proc2.append(subprocess.Popen("python3 bitshares_data.py init", shell=True))

	# operations listener
	#proc2.append(subprocess.Popen("python3 bitshares_data.py operations_listener", shell=True))

	app.add_task(feeder())

	app.run(host="0.0.0.0", port=PORT, workers=1)

	proc1.kill()
	time.sleep(1)
	for p in proc2:
		p.kill()
	time.sleep(1)
