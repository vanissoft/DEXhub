#
# (c) 2018 elias/vanissoft
#
#
#
"""
Features:
	Dynamic building of vertical tabs
	Scrolling tabs
	Dynamic creation of echarts
	Filtering on jQuery.DataTables
"""

from browser import window, document
import w_mod_graphs
import wmodgeneral
import datetime
import json

jq = window.jQuery

Module_name = "marketcharts"

Objcharts = {}
MarketTab = {}
MarketTab2 = {}
ChartData = {}
Order_pos = {}
Order_id_list = {}  # order's ids and account
Order_id_deleted = [] # list of deleted order's ids
Ws_comm = None


#TODO: query for more active pairs


def init(comm):
	global Ws_comm
	Ws_comm = comm
	Ws_comm.send({'call': 'get_tradestats_pair', 'module': Module_name, 'operation': 'enqueue'})



def on_tabshown(ev):
	id = int(ev.target.hash.split("-")[1])

	market = MarketTab2[id]
	Ws_comm.send({'call': 'get_last_trades', 'market': market,
		'date_from': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
		'date_to': datetime.datetime.now().isoformat(),
		'module': Module_name, 'operation': 'enqueue_bg'})

	if market not in ChartData:
		Ws_comm.send({'call': 'get_orderbook', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
		return

	jq("#echart1").show()
	ograph = window.echarts.init(document.getElementById("echart1"))
	og = w_mod_graphs.OrderBook1(ograph)
	og.title = market + " orderbook"
	og.market = market
	#og.orders = Order_pos[market]
	og.load_data(ChartData[market])
	jq("#echart2").show()


def create_tab(num, name, market, badge1):
	tab1 = """<li class=""><a data-toggle="tab" href="#tab-{}" aria-expanded="false">{}<span class="badge pull-right">{}</span></a></li>""".format(num, name, str(badge1))
	document["nav1"].innerHTML += tab1
	MarketTab[market] = num
	MarketTab2[num] = market
	jq('.nav-tabs a').on('shown.bs.tab', on_tabshown)



def onResize():
	pass



def incoming_data(data):
	global Order_pos, Order_id_list
	if data['module'] != Module_name and data['module'] != 'general':  # ignore if nothing to do here
		return
	print("wmodmarketcharts incoming", list(data.keys()))
	if 'stats_pair' in data:
		dat = json.loads(data['stats_pair'])
		cols = ['Pair', 'Ops', 'Pays amount', 'Receives amount', 'Price']
		print(dat[:5])
		for t in enumerate(dat):
			create_tab(t[0]+2, t[1][0], t[1][0], "{0:,.2f}".format(t[1][3]))

		# enqueue orderbooks query
		#TODO: temporally deactivated
		if False:
			for l in dat[:3]:
				Ws_comm.send({'call': 'get_orderbook', 'market': l[0], 'module': Module_name, 'operation': 'enqueue_bg'})

	elif 'orderbook' in data:
		print('a2')
		market = data['orderbook']['market']
		maxv = data['orderbook']['data'][0][3]
		data['orderbook']['data'].insert(0, ['buy', 0, 0, maxv])
		ChartData[market] = data['orderbook']['data']

	elif 'market_trades' in data:
		print('a3')
		print("market_trades received")
		market = data['market_trades']['market']
		ograph = window.echarts.init(document.getElementById("echart2"))
		og = w_mod_graphs.MarketTrades1(ograph)
		og.title = market + " trades"
		og.market = market
		if market in Order_pos:
			og.orders = Order_pos[market]
		og.load_data(data['market_trades']['data'])

	elif 'balances' in data:
		print("----- balances")
		for b in data['balances']:
			print(b)
