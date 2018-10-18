#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document
import datetime
import w_mod_graphs
import wglobals
import json
import random

jq = window.jQuery

Module_name = "marketpanels"
Comm = None

Panels = {}
Panel_count = 0
Order_pos = {}

def save_layout():
	global Comm, Panels
	spanels = [[Panels[p][k] for k in ['market', 'column', 'chart_type']] for p in Panels]
	Comm.send({'call': 'marketpanels_savelayout', 'data': json.dumps(spanels), 'module': "marketpanels", 'operation': 'enqueue'})


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
	save_layout()


def query_market(mkt, chart_type):
	global Comm
	if chart_type == "trades":
		Comm.send({'call': 'get_last_trades', 'market': mkt,
			'date_from': (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat(),
			'date_to': datetime.datetime.now().isoformat(),
			'module': Module_name, 'operation': 'enqueue_bg'})

	elif chart_type == "depth":
		Comm.send({'call': 'get_orderbook', 'market': mkt, 'module': Module_name, 'operation': 'enqueue_bg'})


def new_panel(market, column, chart_type, data=None):
	"""
	Create a new panel in column 0
	"""
	global Panel_count, Panels, Comm
	column = str(column)
	Panel_count += 1
	id = str(Panel_count)
	if chart_type == "trades":
		title = market + " trades"
	elif chart_type == "depth":
		title = market + " depth"
	p1 = panel(Panel_count, market, column, title)
	Panels[id] = {}
	Panels[id]['id'] = id
	Panels[id]['market'] = market
	Panels[id]['column'] = column
	Panels[id]['echart_obj'] = None
	Panels[id]['chart_type'] = chart_type
	Panels[id]['data'] = data
	Panels[id]['next_refresh'] = datetime.datetime.now() + datetime.timedelta(hours=12)
	document['newpanel_'+column].outerHTML = p1
	jq("#form" + str(Panel_count)).hide()
	document['iMarket_' + id].value = market
	document["bChangeMarket1_" + id].bind("click", click_new_trades)
	document["bChangeMarket2_" + id].bind("click", click_new_depth)
	document["bFilter_" + id].bind("click", click_show)
	document["bClose_" + id].bind("click", click_close)
	if data == None:
		query_market(market, chart_type)




def click_close(ev):
	global Panels
	id = str(ev.target.id.split("_")[1])
	document['panel_'+id].outerHTML = ''
	del Panels[id]
	save_layout()


def click_show(ev):
	id = str(ev.target.id.split("_")[1])
	jq("#form"+id).toggle("fast")


def click_new_trades(ev):
	"""
	:param ev:
	:return:
	"""
	id = str(ev.target.id.split("_")[1])
	jq("#form"+id).hide()
	new_panel(document['iMarket_'+id].value, Panels[id]['column'], "trades")
	save_layout()


def click_new_depth(ev):
	"""
	:param ev:
	:return:
	"""
	id = str(ev.target.id.split("_")[1])
	jq("#form"+id).hide()
	new_panel(document['iMarket_'+id].value, Panels[id]['column'], "depth")
	save_layout()


def refresh_data():
	global Panels
	now = datetime.datetime.now()
	for p in Panels:
		if now > Panels[p]['next_refresh']:
			jq("#loading_" + p).show()
			query_market(Panels[p]['market'], Panels[p]['chart_type'])
			Panels[p]['next_refresh'] = datetime.datetime.now() + datetime.timedelta(seconds=random.randint(60, 600))


def init(comm):
	global Comm, Panels, Panel_count
	# globals survive between module calls, clean
	Comm = comm
	Comm.send({'call': 'open_positions', 'module': "general", 'operation': 'enqueue'})
	print("init---------")
	print(Panel_count)
	Panels = {}
	Comm.send({'call': 'marketpanels_loadlayout', 'module': "general", 'operation': 'enqueue'})

	jq('.draggable-container [class*=col]').sortable({"handle": ".panel-body", "connectWith": "[class*=col]",
		"receive": drag_receive,
		"tolerance": 'pointer', "forcePlaceholderSize": True, "opacity": 0.8}).disableSelection()
	wglobals.set_timer(0, refresh_data, 5)


def panel(id, mkt, column, title):
	html = """<div id="newpanel_{2}"></div>
			<p></p>
	       <div class="panel panel-filled" id="panel_{0}">
		       <div class="panel-heading" id="panelheading_{0}">
	                <div class="panel-tools">
	                    <a role="button" id="bFilter_{0}" class="fa fa-filter"></a>
	                    <a role="button" id="bClose_{0}" class="fa fa-times"></a>
	                </div>
	                {3}
	                <div id="loading_{0}" class="loader_example">
	                    <div class="loader-dots"></div>
	                </div>
	            </div>
	            <div class="panel-body" id="panelbody_{0}">
	                <div id="form{0}" class="input-group">
		                <div class="input-group">
		                    <input type="text" class="form-control width100" id="iMarket_{0}" placeholder="xxx/xxx">
		                    <span class="input-group-btn">
		                        <button id="bChangeMarket1_{0}" class="btn btn-accent">Trades</button>
		                        <button id="bChangeMarket2_{0}" class="btn btn-accent">Depth</button>
		                    </span>
		                </div>
		                <hr>
		            </div>
	                <div id="echart_{0}" style="width:100%; height:150px; display: none;"></div>
	            </div>
            </div>"""
	return html.format(str(id), mkt, column, title)



def incoming_data(data):
	global Panels, Order_pos
	if 'pong' in data:
		print("pong!------")

	elif 'market_trades' in data:
		market = data['market_trades']['market']
		print('market_trades', )
		for p in Panels:
			if Panels[p]['market'] == market and Panels[p]['chart_type'] == "trades":
				jq("#loading_" + p).hide()
				jq("#echart_" + p).show()
				obj = window.echarts.init(document.getElementById("echart_"+p))
				og = w_mod_graphs.MarketTrades1('ohlc', obj, None)
				og.market = market
				Panels[p]['echart_obj'] = obj
				Panels[p]['wmgraph_obj'] = og
				Panels[p]['data'] = data
				Panels[p]['next_refresh'] = datetime.datetime.now() + datetime.timedelta(seconds=random.randint(60,600))
				og.load_data(Panels[p]['data']['market_trades']['data'])

	elif 'orderbook' in data:
		market = data['orderbook']['market']
		maxv = data['orderbook']['data'][0][3]
		data['orderbook']['data'].insert(0, ['buy', 0, 0, maxv])
		for p in Panels:
			if Panels[p]['market'] == market and Panels[p]['chart_type'] == "depth":
				jq("#loading_" + p).hide()
				jq("#echart_" + p).show()
				obj = window.echarts.init(document.getElementById("echart_"+p))
				og = w_mod_graphs.OrderBook1('orderbook', obj)
				og.market = market
				if market in Order_pos:
					og.orders = Order_pos[market]
				Panels[p]['echart_obj'] = obj
				Panels[p]['wmgraph_obj'] = og
				Panels[p]['data'] = data
				Panels[p]['next_refresh'] = datetime.datetime.now() + datetime.timedelta(seconds=random.randint(60,600))
				og.load_data({'data': Panels[p]['data']['orderbook']['data']})

	elif 'marketpanels_layout' in data:
		print("layout:", data['marketpanels_layout'])
		for panel in data['marketpanels_layout']:
			print(panel)
			if len(panel) < 3:  # compatibility
				new_panel(panel[0], panel[1], "depth")
			else:
				new_panel(panel[0], panel[1], panel[2])

	elif 'open_positions' in data:
		if data['open_positions'] is None:
			return
		dat1 = data['open_positions']
		dat1.sort(key=lambda x: x[0]+x[3]+x[1])
		markets = dict()
		dat = []
		Order_pos = {}
		for d in dat1:
			tmpl1 = "{:,."+str(d[8])+"f}"
			tmpl2 = "{:,."+str(d[9])+"f}"
			market = d[1]+"/"+d[3]
			dat.append([market, d[0], tmpl1.format(d[2]), tmpl2.format(d[5]), tmpl2.format(d[6]), d[7]])
			if market in markets:
				Order_pos[market].append([d[0], d[5]])
			else:
				Order_pos[market] = [[d[0], d[5]]]

