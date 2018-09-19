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
import wmodules

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
		['market_charts.html', 'wmodmarketcharts'],
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

wglobals.Menu_binds = {'link_'+k.split('.')[0].lower(): k for (k,v) in Binds}
wglobals.Page_binds = {k: v for (k,v) in Binds}



def ws_received(data):
	if wglobals.Active_module is not None:
		print("wmain.ws_received ",data['module'], "active:", wglobals.Active_module.Module_name)
	if 'message' in data:
		wmodgeneral.message(data)
	elif data['module'] == 'general':
		wmodgeneral.incoming_data(data)
	else:
		if data['module'] != wglobals.Active_module.Module_name:
			if data['module'] not in wglobals.Incoming_data:
				wglobals.Incoming_data[data['module']] = []
				wglobals.Incoming_data[data['module']].append(data)
		else:
			#print(data['module'], Active_module.Module_name)
			wglobals.Active_module.incoming_data(data)

window.toastr.info('Welcome to DEX HUB<br>A Bitshares portfolio manager.', None, {"debug": 0, "newestOnTop": 1, "positionClass": "toast-top-center", "closeButton": 1, "progressBar": True})


wglobals.Ws_comm = wwebsockets.Wscomm("ws://127.0.0.1:8808/comm", ws_received)


def init_data():
	if wglobals.Ws_comm.open:
		#wglobals.Ws_comm.send({'call': 'open_positions', 'module': "general", 'operation': 'enqueue_bg'})
		#Ws_comm.send({'call': 'get_balances', 'module': "general", 'operation': 'enqueue_bg'})
		wglobals.clear_timer(0)
	wmodgeneral.Data.data['master_unlocked'] = False

# one time initialisation
wglobals.set_timer(0, init_data, 0.5)


def master_unlock(ev):
	print("unlock:", document["iMPpasshrase"].value)
	#document['MPerror'].innerHTML = "Password doesn't match?<br>Not implemented"
	wglobals.Ws_comm.send({'call': 'master_unlock', 'data': document["iMPpasshrase"].value, 'module': "general", 'operation': 'enqueue'})


def show_status(ev):
	jq('#infopanel1').toggleClass('hidden')

# bind menu links
for bind in wglobals.Menu_binds.items():
	try:
		document[bind[0]].bind('click', wmodules.menu_click)
	except Exception as err:
		print(err)

document["bMPunlock"].bind('click', master_unlock)
document["bShowStatus"].bind('click', show_status)

