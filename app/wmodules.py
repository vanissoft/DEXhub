#
# (c) 2017 elias/vanissoft
#
#
#


from browser import window, document, ajax, alert
import wglobals

import json
from functools import partial

jq = window.jQuery


Cnt = 0




def html_loaded(url, rtn):
	page = url.split('&')[0]
	print("url", url)
	print("url", rtn)
	document['page_container'].innerHTML = rtn
	try:
		wglobals.Active_module = __import__(wglobals.Page_binds[page])
	except Exception as err:
		print("error:", err.__repr__())
		return False
	if wglobals.Active_module is not None:
		wglobals.Ws_comm.send("change from client")
		wglobals.Ws_comm.send({'operation': 'module_activation', 'module': wglobals.Active_module.Module_name})
		print("activate", wglobals.Active_module.Module_name)
		if wglobals.Active_module in wglobals.Incoming_data:
			while len(wglobals.Incoming_data[wglobals.Active_module])> 0:
				wglobals.Active_module.incoming_data(wglobals.Incoming_data[wglobals.Active_module].pop())

		wglobals.Active_module.init(wglobals.Ws_comm)


def change_module():
	#TODO: locate menu div from link_xxxx
	pass

def menu_click(ev):
	wglobals.clear_timer(0)
	jq("ul > li").removeClass('active')
	jq(ev.target.parent).addClass('active')
	query(wglobals.Menu_binds[ev.target.id], html_loaded)


def query(url, callback):
	global Cnt
	url = url+"&nonce="+str(Cnt)
	wglobals.Callbacks[url] = callback
	req = ajax.ajax()
	req.open('GET', url, True)
	req.send()
	func = partial(ajax_end, url)
	req.bind('complete', func)
	Cnt += 1


def ajax_end(url, request):
	global Cnt
	if request.responseText[0] == '{':
		try:
			rtn = json.loads(request.responseText)
		except Exception as err:
			print(err.__repr__())
			return
		if rtn is None:
			print("error\n"+request.responseText)
			return
		print(rtn['request'])
		if rtn['request'] in wglobals.Callbacks:
			print("callback ok")
			wglobals.Callbacks[rtn['request']](rtn)
			del wglobals.Callbacks[rtn['request']]
	else:
		wglobals.Callbacks.popitem()[1](url, request.responseText)

