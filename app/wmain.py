#
# (c) 2017 elias/vanissoft
#
#
#


from browser import window, document, ajax, alert
import wwebsockets
import wglobals
import wmodgeneral

import json
from functools import partial

jq = window.jQuery



# page, link in navigation.html, module
Binds = [['dashboard.html', 'wmoddashboard'],
		['limit_orders.html', 'wmodlimitorders'],
		['marketpanels.html', 'wmodmarketpanels'],
		['dataTables.html', 'wmoddatatables'],
		['settings.html', 'wmodsettings'],
		['balances.html', 'wmodbalances'],
		['order_repos.html', 'wmodorderrepos'],
		['limit_orders.html', 'wmodlimitorders'],
		['trades_statistics.html', 'wmodtstats'],
		['tradehistory.html', 'wmodtradehistory'],
		['metrics.html', ''],
		['usage.html', ''],
		['activity.html', ''],
		['panels.html', ''],
		['profile.html', ''],
		['contacts.html', ''],
		['projects.html', ''],
		['support.html', ''],
		['nestablelist.html', ''],
		['timeline.html', ''],
		['login.html', ''],
		['register.html', ''],
		['forgotpassword.html', ''],
		['typography.html', ''],
		['icons.html', ''],
		['buttons.html', ''],
		['tabs.html', ''],
		['modals.html', ''],
		['alerts.html', ''],
		['loaders.html', ''],
		['gridSystem.html', ''],
		['tableStyles.html', ''],
		['formElements.html', ''],
		['autocomplete.html', ''],
		['controls.html', ''],
		['textEditor.html', ''],
		['flotCharts.html', ''],
		['chartJs.html', ''],
		['sparkline.html', ''],
		['datamaps.html', ''],
		['versions.html', ''],
		['error.html', '']
		 ]

Menu_binds = {'link_'+k.split('.')[0].lower(): k for (k,v) in Binds}
Page_binds = {k: v for (k,v) in Binds}

Cnt = 0
Callbacks = {}
Active_module = None
Incoming_data = {}


def ws_received(data):
	global Ws_comm
	print("incoming ",data['module'], "active:", Active_module.Module_name)
	if 'message' in data:
		wmodgeneral.message(data)
	elif data['module'] == 'general':
		wmodgeneral.incoming_data(data)
	else:
		if data['module'] != Active_module.Module_name:
			if data['module'] not in Incoming_data:
				Incoming_data[data['module']] = []
			Incoming_data[data['module']].append(data)
		else:
			print(data['module'], Active_module.Module_name)
			Active_module.incoming_data(data)

Ws_comm = wwebsockets.Wscomm("ws://127.0.0.1:8808/comm", ws_received)


def init_data():
	if Ws_comm.open:
		Ws_comm.send({'call': 'open_positions', 'module': "general", 'operation': 'enqueue'})
		Ws_comm.send({'call': 'get_balances', 'module': "general", 'operation': 'enqueue'})
		wglobals.clear_timer(0)

# one time initialisation
wglobals.set_timer(0, init_data, 0.1)


def html_loaded(url, rtn):
	global Ws_comm, Active_module
	page = url.split('&')[0]
	print("url", url)
	document['page_container'].innerHTML = rtn
	try:
		Active_module = __import__(Page_binds[page])
	except Exception as err:
		print("error:", err.__repr__())
		return False
	if Active_module is not None:
		Ws_comm.send("change from client")
		Ws_comm.send({'operation': 'module_activation', 'module': Active_module.Module_name})
		print("activate", Active_module.Module_name)
		if Active_module in Incoming_data:
			while len(Incoming_data[Active_module])> 0:
				Active_module.incoming_data(Incoming_data[Active_module].pop())

		Active_module.init(Ws_comm)


def menu_click(ev):
	global Menu_binds, Ws_comm
	wglobals.clear_timer(0)
	jq("ul > li").removeClass('active')
	jq(ev.target.parent).addClass('active')
	query(Menu_binds[ev.target.id], html_loaded)


def query(url, callback):
	global Cnt
	url = url+"&nonce="+str(Cnt)
	Callbacks[url] = callback
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
		if rtn['request'] in Callbacks:
			print("callback ok")
			Callbacks[rtn['request']](rtn)
			del Callbacks[rtn['request']]
	else:
		Callbacks.popitem()[1](url, request.responseText)


def master_unlock(ev):
	print("unlock:", document["iMPpasshrase"].value)
	#document['MPerror'].innerHTML = "Password doesn't match?<br>Not implemented"
	Ws_comm.send({'call': 'master_unlock', 'data': document["iMPpasshrase"].value, 'module': "general", 'operation': 'enqueue'})


def show_status(ev):
	jq('#infopanel1').toggleClass('hidden')

# bind menu links
for bind in Menu_binds.items():
	try:
		document[bind[0]].bind('click', menu_click)
	except Exception as err:
		print(err)

document["bMPunlock"].bind('click', master_unlock)
document["bShowStatus"].bind('click', show_status)

window.toastr.info('Welcome to DEX HUB<br>A Bitshares portfolio manager.', None, {"debug": 0, "newestOnTop": 1, "positionClass": "toast-top-center", "closeButton": 1, "progressBar": True})
