#
# (c) 2017 elias/vanissoft
#
#

from browser import window, alert
import json

class Wscomm():

	def __init__(self, uri, recv_callback=None):
		self.callback = recv_callback
		WebSocket = window.WebSocket.new
		self.ws = WebSocket(uri)
		# bind functions to web socket events
		self.ws.bind('open', self._on_open)
		self.ws.bind('message', self._on_message)
		self.ws.bind('close', self._on_close)
		self.open = False

	def _on_open(self, evt):
		self.open = True

	def _on_message(self, evt):
		try:
			#print("ws received", evt.data, type(evt.data))
			data = json.loads(evt.data)
			if self.callback is not None:
				self.callback(data)
		except Exception as err:
			if 'Unexpected' in err.__repr__():
				pos = int(err.__repr__().split(" ")[-1].split(">")[0])
				print("error pos:", evt.data[pos-10:pos+10])
			print("ws error evt.data", evt.data[:100], evt.data[-100:])
			print("ws error:", err.__repr__())

	def _on_close(self, evt):
		alert("Connection is closed")

	def send(self, data):
		print("ws send:", data)
		self.ws.send(json.dumps(data))

	def _close_connection(self):
		self.ws.close()

