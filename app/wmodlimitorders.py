#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document
import w_mod_graphs
import datetime

jq = window.jQuery

Module_name = "limitorders"

Objcharts = {}
MarketTab = {}
MarketTab2 = {}
ChartData = {}
Order_pos = {}
Ws_comm = None

def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	Ws_comm.send({'operation': 'enqueue', 'module': "main", 'what': 'open_positions'})
	document["bReloadOrders"].bind('click', click_reload_orders)
	document["bBalances"].bind('click', click_balances)
	jq("#echartx").hide()
	jq("#echarty").hide()

def click_reload_orders(ev):
	Ws_comm.send({'operation': 'enqueue', 'module': "main", 'what': 'open_positions'})

def click_balances(ev):
	Ws_comm.send({'operation': 'enqueue', 'module': "main", 'what': 'get_balances'})

def on_tabshown(ev):
	id = int(ev.target.hash.split("-")[1])
	if id == 1:
		jq('#tableExample1').DataTable().search('').draw()
		jq("#echartx").hide()

	market = MarketTab2[id]
	Ws_comm.send({'operation': 'enqueue', 'module': Module_name, 'what': 'get_market_trades', 'market': market,
		'date_from': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
		'date_to': datetime.datetime.now().isoformat()})

	if market not in ChartData:
		return

	jq("#echartx").show()
	ograph = window.echarts.init(document.getElementById("echartx"))
	og = w_mod_graphs.OrderBook1(ograph)
	og.title = market + " orderbook"
	og.market = market
	og.orders = Order_pos[market]
	og.load_data(ChartData[market])
	jq('#tableExample1').DataTable().search(market).draw()


def create_tab(num, name, market, badge1):
	tab1 = """<li class=""><a data-toggle="tab" href="#tab-{}" aria-expanded="false">{}<span class="badge pull-right">{}</span></a></li>""".format(num, name, str(badge1))
	document["nav1"].innerHTML += tab1
	MarketTab[market] = num
	MarketTab2[num] = market
	jq('.nav-tabs a').on('shown.bs.tab', on_tabshown)



def onResize():
	pass

def incoming_data(data):
	global Order_pos
	# [market, 'sell', "{0:,.5f}".format(q1), "{0:,.8f}".format(q2 / q1), "{0:,.5f}".format(q2), t[1]]
	print('module', Module_name, "incoming_data")
	if 'open_positions' in data['data']:

		if data['data']['open_positions'] is None:
			return

		#jq('#panel1').addClass('ld-loading')
		cols = "Market,Operation,Quantity,Price,Total,Date"
		dat1 = data['data']['open_positions']
		dat1.sort(key=lambda x: x[0]+x[3]+x[1])
		markets = dict()

		# populate table
		print(dat1[-2:])
		dat = []
		for d in dat1:
			tmpl1 = "{:,."+str(d[8])+"f}"
			tmpl2 = "{:,."+str(d[9])+"f}"
			market = d[1]+"/"+d[3]
			dat.append([market, d[0], tmpl1.format(d[2]), tmpl2.format(d[5]), tmpl2.format(d[6]), d[7]])
			if market in markets:
				markets[market] += 1
				Order_pos[market].append([d[0], d[5]])
			else:
				markets[market] = 1
				Order_pos[market] = [[d[0], d[5]]]

		# create tabs
		lmkts = list(markets.keys())
		lmkts.sort()
		for t in enumerate(lmkts):
			create_tab(t[0]+2, t[1], t[1], markets[t[1]])

		# enqueue orderbooks query
		for l in lmkts[:]:
			Ws_comm.send({'operation': 'enqueue_bg', 'module': Module_name, 'what': 'orderbook', 'market': l})

		jq('#tableExample1').DataTable({"data": dat, "columns": [{'title': v} for v in cols.split(",")],
			"dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
			"lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
			"buttons": [{"extend": 'copy', "className": 'btn-sm'},
						{"extend": 'csv', "title": 'ExampleFile', "className": 'btn-sm'},
						{"extend": 'pdf', "title": 'ExampleFile', "className": 'btn-sm'},
						{"extend": 'print', "className": 'btn-sm'}]})
		#jq('#panel1').removeClass('ld-loading')

	elif 'orderbook' in data['data']:
		print(data['data']['orderbook']['date'], data['data']['orderbook']['market'], data['data']['orderbook']['data'][0])
		market = data['data']['orderbook']['market']
		maxv = data['data']['orderbook']['data'][0][3]
		data['data']['orderbook']['data'].insert(0, ['buy', 0, 0, maxv])
		ChartData[market] = data['data']['orderbook']['data']

	elif 'market_trades' in data['data']:
		jq("#echarty").show()
		print("Market trades received")
		print(data['data']['market_trades']['market'])
		print(data['data']['market_trades']['market'], len(data['data']['market_trades']['data']))
		print(data['data']['market_trades']['data'][0], len(data['data']['market_trades']['data']))
		market = data['data']['market_trades']['market']
		ograph = window.echarts.init(document.getElementById("echarty"))
		og = w_mod_graphs.MarketTrades1(ograph)
		og.title = market + " trades"
		og.market = market
		og.orders = Order_pos[market]
		og.load_data(data['data']['market_trades']['data'])

	elif 'balances' in data['data']:
		print("----- balances")
		for b in data['data']['balances']:
			print(b)
