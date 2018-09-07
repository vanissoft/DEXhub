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
ChartData_trades = {}
ChartData_ob = {}
ChartData_analisis1 = {}
ChartData_analisis2 = {}
ChartData_analisis3 = {}
ChartData_analisis4 = {}
Order_pos = {}
Order_id_list = {}  # order's ids and account
Order_id_deleted = [] # list of deleted order's ids
Ws_comm = None
Last_Pair = ''


def init(comm):
	global Ws_comm
	Ws_comm = comm
	Ws_comm.send({'call': 'get_tradestats_pair', 'module': Module_name, 'operation': 'enqueue'})
	document["bRefresh"].bind('click', refresh)
	document["bRefreshAll"].bind('click', refresh_all)

def refresh(ev):
	global ChartData_trades, ChartData_analisis1, ChartData_analisis2, ChartData_ob
	print("refresh")
	if Last_Pair != '':
		del ChartData_trades[Last_Pair]
		del ChartData_analisis1[Last_Pair]
		del ChartData_analisis2[Last_Pair]
		del ChartData_analisis3[Last_Pair]
		del ChartData_analisis4[Last_Pair]
		del ChartData_ob[Last_Pair]
		ask_data(Last_Pair)

def refresh_all(ev):
	global ChartData_trades, ChartData_analisis1, ChartData_analisis2, ChartData_analisis3, ChartData_analisis4, ChartData_ob
	print("refresh all")
	ChartData_trades = {}
	ChartData_analisis1 = {}
	ChartData_analisis2 = {}
	ChartData_analisis3 = {}
	ChartData_analisis4 = {}
	ChartData_ob = {}


def axis_sync(name, ochart, opts):
	def nearest(list1, txt):
		for l in enumerate(list1):
			if l[1] >= txt:
				return l[0]
		return len(list1)-1
	print(name)
	print(1, opts.axisPointer[0].value)
	print(2, opts.xAxis[0].axisPointer.value)
	print(2, opts.yAxis[0].axisPointer.value)
	print(opts.xAxis[0].data[opts.xAxis[0].axisPointer.value])
	date = opts.xAxis[0].data[opts.xAxis[0].axisPointer.value]
	def update_axis(name, date):
		if name not in Objcharts:
			return
		opt = Objcharts[name].getOption()
		opt.xAxis[0].axisPointer.value = nearest(opt.xAxis[0].data, date)
		opt.xAxis[0].axisPointer.show = True
		opt.xAxis[0].axisPointer.status = True
		Objcharts[name].setOption({"xAxis": opt.xAxis})

	charts = ['chart' + str(n) for n in [2, 3, 4, 5, 6]]

	if name == 'wavetrends':
		charts.remove('chart3')
	elif name == 'stoch-rsi':
		charts.remove('chart4')
	elif name == 'ohlc':
		charts.remove('chart2')
	elif name == 'rsi':
		charts.remove('chart5')
	elif name == 'cci':
		charts.remove('chart6')
	else:
		return
	for chart in charts:
		update_axis(chart, date)


def chart1(pair):
	jq("#echart1").show()
	ograph = window.echarts.init(document.getElementById("echart1"))
	og = w_mod_graphs.OrderBook1(ograph)
	og.title = pair + " orderbook"
	og.market = pair
	#og.orders = Order_pos[pair]
	og.load_data(ChartData_ob[pair])

def chart2(pair):
	Objcharts['chart2'] = window.echarts.init(document.getElementById("echart2"))
	og = w_mod_graphs.MarketTrades1('ohlc', Objcharts['chart2'], axis_sync)
	og.title = pair + " trades"
	og.market = pair
	if pair in Order_pos:
		og.orders = Order_pos[pair]
	og.load_data(ChartData_trades[pair])

def chart3(pair):
	jq("#echart3").show()
	Objcharts['chart3'] = window.echarts.init(document.getElementById("echart3"))
	og = w_mod_graphs.SeriesSimple('wavetrends', Objcharts['chart3'], axis_sync)
	og.driven = False
	og.title = pair + " wavetrends"
	og.market = pair
	og.hard_limits_y = [-80, 80]
	og.load_data(ChartData_analisis1[pair])


def chart4(pair):
	jq("#echart4").show()
	Objcharts['chart4'] = window.echarts.init(document.getElementById("echart4"))
	og = w_mod_graphs.SeriesSimple('stoch-rsi', Objcharts['chart4'], axis_sync)
	og.driven = False
	og.title = pair + " stoch-rsi"
	og.market = pair
	og.hard_limits_y = [0, 100]
	og.load_data(ChartData_analisis2[pair])


def chart5(pair):
	jq("#echart5").show()
	Objcharts['chart5'] = window.echarts.init(document.getElementById("echart5"))
	og = w_mod_graphs.SeriesSimple('rsi', Objcharts['chart5'], axis_sync)
	og.driven = False
	og.title = pair + " rsi"
	og.market = pair
	og.hard_limits_y = [20, 80]
	og.load_data(ChartData_analisis3[pair])


def chart6(pair):
	jq("#echart6").show()
	Objcharts['chart6'] = window.echarts.init(document.getElementById("echart6"))
	og = w_mod_graphs.SeriesSimple('cci', Objcharts['chart6'], axis_sync)
	og.driven = False
	og.title = pair + " cci"
	og.market = pair
	og.hard_limits_y = [-300, 300]
	og.load_data(ChartData_analisis4[pair])


def ask_data(market):
	if market not in ChartData_trades:
		Ws_comm.send({'call': 'get_last_trades', 'market': market,
			'date_from': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
			'date_to': datetime.datetime.now().isoformat(),
			'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart2(market)

	if market not in ChartData_analisis1:
		Ws_comm.send({'call': 'analysis_wavetrend', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart3(market)
		jq("#echart3").show()

	if market not in ChartData_analisis2:
		Ws_comm.send({'call': 'analysis_stoch_rsi', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart4(market)
		jq("#echart4").show()

	if market not in ChartData_analisis3:
		Ws_comm.send({'call': 'analysis_rsi', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart5(market)
		jq("#echart5").show()

	if market not in ChartData_analisis4:
		Ws_comm.send({'call': 'analysis_cci', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart6(market)
		jq("#echart6").show()

	if market not in ChartData_ob:
		Ws_comm.send({'call': 'get_orderbook', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart1(market)
		jq("#echart1").show()



def on_tabshown(ev):
	global Last_Pair

	id = int(ev.target.hash.split("-")[1])

	market = MarketTab2[id]
	Last_Pair = market
	ask_data(market)



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
		market = data['orderbook']['market']
		maxv = data['orderbook']['data'][0][3]
		data['orderbook']['data'].insert(0, ['buy', 0, 0, maxv])
		ChartData_ob[market] = data['orderbook']['data']
		chart1(market)

	elif 'market_trades' in data:
		Last_Pair = data['market_trades']['market']
		ChartData_trades[data['market_trades']['market']] = data['market_trades']['data']
		chart2(data['market_trades']['market'])

	elif 'analysis_wavetrend' in data:
		Last_Pair = data['analysis_wavetrend']['market']
		ChartData_analisis1[data['analysis_wavetrend']['market']] = data['analysis_wavetrend']['data']
		chart3(data['analysis_wavetrend']['market'])

	elif 'analysis_stoch_rsi' in data:
		Last_Pair = data['analysis_stoch_rsi']['market']
		ChartData_analisis2[data['analysis_stoch_rsi']['market']] = data['analysis_stoch_rsi']['data']
		chart4(data['analysis_stoch_rsi']['market'])

	elif 'analysis_rsi' in data:
		Last_Pair = data['analysis_rsi']['market']
		ChartData_analisis3[data['analysis_rsi']['market']] = data['analysis_rsi']['data']
		chart5(data['analysis_rsi']['market'])

	elif 'analysis_cci' in data:
		Last_Pair = data['analysis_cci']['market']
		ChartData_analisis4[data['analysis_cci']['market']] = data['analysis_cci']['data']
		chart6(data['analysis_cci']['market'])

