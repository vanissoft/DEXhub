#
# (c) 2017 elias/vanissoft
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

jq = window.jQuery

Module_name = "limitorders"

Objcharts = {}
MarketTab = {}
MarketTab2 = {}
ChartData = {}
Order_pos = {}
Order_id_list = {}  # order's ids and account
Order_id_deleted = [] # list of deleted order's ids
Ws_comm = None

#TODO: datatables destroy prior to recharge


def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	Ws_comm.send({'call': 'open_positions', 'module': Module_name, 'operation': 'enqueue_bg'})
	document["bReloadOrders"].bind('click', click_reload_orders)
	document["bBalances"].bind('click', click_balances)
	jq("#echartx").hide()
	jq("#echarty").hide()

def click_reload_orders(ev):
	Ws_comm.send({'call': 'open_positions', 'module': Module_name, 'operation': 'enqueue_bg'})

def click_balances(ev):
	Ws_comm.send({'call': 'get_balances', 'module': Module_name, 'operation': 'enqueue_bg'})

def click_delete_order(ev):
	global Order_id_deleted
	id = ev.target.id.split("_")[1]
	Order_id_deleted.append(id)
	print("delete order", id, 'account:', Order_id_list[id])
	Ws_comm.send({'call': 'order_delete', 'id': id, 'account': Order_id_list[id], 'module': Module_name, 'operation': 'enqueue'})
	jq('#tableExample1').DataTable().rows().invalidate('data')
	jq('#tableExample1').DataTable().draw(False)


def on_tabshown(ev):
	id = int(ev.target.hash.split("-")[1])
	if id == 1:
		jq('#tableExample1').DataTable().search('').draw()
		jq("#echartx").hide()
		jq("#echarty").hide()
		return

	market = MarketTab2[id]
	Ws_comm.send({'call': 'get_last_trades', 'market': market,
		'date_from': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
		'date_to': datetime.datetime.now().isoformat(),
		'module': Module_name, 'operation': 'enqueue_bg'})

	if market not in ChartData:
		return

	jq("#echartx").show()
	ograph = window.echarts.init(document.getElementById("echartx"))
	og = w_mod_graphs.OrderBook1(ograph)
	og.title = market + " orderbook"
	og.market = market
	og.orders = Order_pos[market]
	og.load_data({'data': ChartData[market]})
	jq('#tableExample1').DataTable().search(market).draw()
	jq("#echarty").show()


def create_tab(num, name, market, badge1):
	tab1 = """<li class=""><a data-toggle="tab" href="#tab-{}" aria-expanded="false">{}<span class="badge pull-right">{}</span></a></li>""".format(num, name, str(badge1))
	document["nav1"].innerHTML += tab1
	MarketTab[market] = num
	MarketTab2[num] = market
	jq('.nav-tabs a').on('shown.bs.tab', on_tabshown)



def onResize():
	pass

def table_drawn(settings):
	for order_id in Order_id_list:
		try:
			if document["bDelOrder_{0}".format(order_id)].events('click'):
				document["bDelOrder_{0}".format(order_id)].unbind('click', click_delete_order)
			document["bDelOrder_{0}".format(order_id)].bind('click', click_delete_order)
		except:
			continue


def incoming_data(data):
	global Order_pos, Order_id_list
	# [market, 'sell', "{0:,.5f}".format(q1), "{0:,.8f}".format(q2 / q1), "{0:,.5f}".format(q2), t[1]]
	if data['module'] != Module_name and data['module'] != 'general':  # ignore if nothing to do here
		return
	if 'open_positions' in data:
		if data['open_positions'] is None:
			return
		dat1 = []
		Order_id_list = {}
		Order_id_deleted = []
		Order_pos = {}
		#jq('#panel1').addClass('ld-loading')
		cols = "Market,Operation,Quantity,Price,Total,cancel"
		dat1.sort(key=lambda x: x[0]+x[3]+x[1])
		markets = dict()

		# populate table
		dat = []
		#[account[0], lo['id'], pair, 'buy', amount_quote, quote, amount_base, base, price, Assets[quote][1],Assets[base][1]])
		for d in data['open_positions']:
			tmpl1 = "{:,."+str(d[9])+"f}"
			tmpl2 = "{:,."+str(d[10])+"f}"
			# {1.7.12321: 'account'}
			Order_id_list[d[1]] = d[0]
			dat.append([d[2], d[3], tmpl1.format(d[4]), tmpl2.format(d[8]), tmpl2.format(d[6]), d[1]])
			if d[2] in markets:
				markets[d[2]] += 1
				# quantity, price
				Order_pos[d[2]].append([d[4], d[8]])
			else:
				markets[d[2]] = 1
				Order_pos[d[2]] = [[d[4], d[8]]]

		# create tabs
		lmkts = list(markets.keys())
		lmkts.sort()
		for t in enumerate(lmkts):
			create_tab(t[0]+2, t[1], t[1], markets[t[1]])

		# enqueue orderbooks query
		for l in lmkts[:]:
			Ws_comm.send({'call': 'get_orderbook', 'market': l, 'module': Module_name, 'operation': 'enqueue_bg'})

		def cell_buttons(data, type, row, meta):
			if data not in Order_id_deleted:
				if wmodgeneral.Data.data['master_unlocked']:
					return '<a role="button" id="bDelOrder_{0}" class="fa fa-times fa-2x"></a>'.format(data)
				else:
					return '<span>not permission</span>'
			else:
				return '<span>deleted</span>'.format(data)

		dt = jq('#tableExample1').DataTable({"data": dat, "columns": [{'title': v} for v in cols.split(",")],
			"dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
			"lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
			"columnDefs": [{"targets": 5, "render": cell_buttons}],
			"drawCallback": table_drawn,
			"buttons": [{"extend": 'copy', "className": 'btn-sm'},
						{"extend": 'csv', "title": 'ExampleFile', "className": 'btn-sm'},
						{"extend": 'pdf', "title": 'ExampleFile', "className": 'btn-sm'},
						{"extend": 'print', "className": 'btn-sm'}]})
		#jq('#panel1').removeClass('ld-loading')


	elif 'orderbook' in data:
		market = data['orderbook']['market']
		maxv = data['orderbook']['data'][0][3]
		data['orderbook']['data'].insert(0, ['buy', 0, 0, maxv])
		ChartData[market] = data['orderbook']['data']

	elif 'market_trades' in data:
		market = data['market_trades']['market']
		ograph = window.echarts.init(document.getElementById("echarty"))
		og = w_mod_graphs.MarketTrades1('trades', ograph, None)
		og.title = market + " trades"
		og.market = market
		og.orders = Order_pos[market]
		og.load_data(data['market_trades']['data'])

	elif 'balances' in data:
		print("----- balances")
		for b in data['balances']:
			print(b)
