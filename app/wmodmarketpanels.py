#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document
import datetime
import w_mod_graphs
import json

jq = window.jQuery

Module_name = "marketpanels"
Comm = None

Panels = {}
Panel_count = 0


def save_layout():
	global Comm, Panels
	spanels = [[Panels[p][k] for k in ['market', 'column']] for p in Panels]
	Comm.send({'operation': 'enqueue', 'module': "marketpanels", 'what': 'marketpanels_savelayout', 'data': json.dumps(spanels)})


def drag_receive(ev, ui):
	global Panels
	column = int(ev.target.id.split("_")[1])
	panel = ui.item.attr("id").split("_")[1]
	print(panel, panel in Panels)
	if panel in Panels:
		Panels[panel]['column'] = column
		print(Panels[panel]['column'], column)
		if Panels[panel]['echart_obj'] is not None:
			Panels[panel]['echart_obj'].resize()
	print("destino:", column)
	print("panels:", Panels)
	save_layout()

def query_market(mkt):
	global Comm
	Comm.send({'operation': 'enqueue', 'module': Module_name, 'what': 'get_market_trades', 'market': mkt,
		'date_from': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
		'date_to': datetime.datetime.now().isoformat()})


def new_panel(market, column):
	"""
	Create a new panel in column 0
	"""
	global Panel_count, Panels, Comm
	column = str(column)
	Panel_count += 1
	p1 = panel(Panel_count, market, column)
	Panels[str(Panel_count)] = {}
	Panels[str(Panel_count)]['market'] = market
	Panels[str(Panel_count)]['column'] = column
	Panels[str(Panel_count)]['echart_obj'] = None
	document['newpanel_'+column].outerHTML = p1
	jq("#form" + str(Panel_count)).hide()
	document["bChangeMarket1_" + str(Panel_count)].bind("click", click_change_market1)
	document["bChangeMarket2_" + str(Panel_count)].bind("click", click_change_market2)
	document["bFilter_" + str(Panel_count)].bind("click", click_show)
	query_market(market)


def populate_panels():
	# TODO: recover from database
	Comm.send({'operation': 'enqueue', 'module': "marketpanels", 'what': 'marketpanels_loadlayout'})
	#new_panel("OPEN.ETH/BTS", 1)


def click_show(ev):
	id = str(ev.target.id.split("_")[1])
	jq("#form"+id).toggle("fast")


def click_change_market1(ev):
	"""
	Change market of the panel
	:param ev:
	:return:
	"""
	global Panels
	id = str(ev.target.id.split("_")[1])
	Panels[id]['market'] = document['iMarket_'+id].value
	query_market(Panels[id]['market'])
	jq("#form"+id).hide("fast")


def click_change_market2(ev):
	"""
	Create a new panel
	:param ev:
	:return:
	"""
	id = str(ev.target.id.split("_")[1])
	jq("#form"+id).hide()
	new_panel(document['iMarket_'+id].value, Panels[id]['column'])


def init(comm):
	global Comm, Panels, Panel_count
	# globals survive between module calls, clean
	Panels = {}
	Panel_count = 0
	Comm = comm
	populate_panels()
	jq('.draggable-container [class*=col]').sortable({"handle": ".panel-body", "connectWith": "[class*=col]",
		"receive": drag_receive,
		"tolerance": 'pointer', "forcePlaceholderSize": True, "opacity": 0.8}).disableSelection()


def panel(id, mkt, column):
	html = """<div id="newpanel_{2}"></div>
			<p></p>
	       <div class="panel panel-filled" id="panel_{0}">
	       <div class="panel-heading">
                <div class="panel-tools">
                    <a role="button" id="bFilter_{0}" class="fa fa-filter"></a>
                </div>
                {1}
            </div>
            <div class="panel-body">
                <div id="form{0}" class="input-group">
                    <input type="text" class="form-control width100" id="iMarket_{0}" placeholder="xxx/xxx">
                    <span class="input-group-btn">
                        <button id="bChangeMarket1_{0}" class="btn btn-accent">Change</button>
                        <button id="bChangeMarket2_{0}" class="btn btn-accent">New Panel</button>
                    </span>
                </div>
                <div id="echart_{0}" style="width:100%; height:250px; display: none;"></div>
            </div>
        </div>"""
	return html.format(str(id), mkt, column)


def onResize():
	pass

def incoming_data(data):
	global Panels
	print("incoming", data['data'])
	if 'market_trades' in data['data']:
		market = data['data']['market_trades']['market']
		for p in Panels:
			if Panels[p]['market'] == market:
				jq("#echart_"+p).show()
				obj = window.echarts.init(document.getElementById("echart_"+p))
				og = w_mod_graphs.MarketTrades1(obj)
				og.title = market + " trades"
				og.market = market
				og.load_data(data['data']['market_trades']['data'])
				Panels[p]['echart_obj'] = obj
				Panels[p]['wmgraph_obj'] = og
	elif 'marketpanels_layout' in data['data']:
		print(data['data']['marketpanels_layout'])
		for panel in data['data']['marketpanels_layout']:
			print(panel)
			new_panel(panel[0], panel[1])
