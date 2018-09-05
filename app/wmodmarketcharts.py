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
Order_pos = {}
Order_id_list = {}  # order's ids and account
Order_id_deleted = [] # list of deleted order's ids
Ws_comm = None


#TODO: query for more active pairs


def init(comm):
	global Ws_comm
	Ws_comm = comm
	Ws_comm.send({'call': 'get_tradestats_pair', 'module': Module_name, 'operation': 'enqueue'})


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
		opt = Objcharts[name].getOption()
		opt.xAxis[0].axisPointer.value = nearest(opt.xAxis[0].data, date)
		opt.xAxis[0].axisPointer.show = True
		opt.xAxis[0].axisPointer.status = True
		Objcharts[name].setOption({"xAxis": opt.xAxis})

	if name == 'wavetrends':
		update_axis('chart2', date)
		update_axis('chart4', date)
	elif name == 'stoch-rsi':
		update_axis('chart2', date)
		update_axis('chart3', date)
	elif name == 'ohlc':
		update_axis('chart3', date)
		update_axis('chart4', date)


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


def on_tabshown(ev):
	id = int(ev.target.hash.split("-")[1])

	market = MarketTab2[id]
	Ws_comm.send({'call': 'get_last_trades', 'market': market,
		'date_from': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),
		'date_to': datetime.datetime.now().isoformat(),
		'module': Module_name, 'operation': 'enqueue_bg'})

	if market not in ChartData_analisis1:
		Ws_comm.send({'call': 'analysis_wavetrend', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart3(market)
		jq("#echart3").show()

	if market not in ChartData_analisis1:
		Ws_comm.send({'call': 'analysis_stoch_rsi', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart4(market)
		jq("#echart4").show()

	if market not in ChartData_trades:
		Ws_comm.send({'call': 'get_orderbook', 'market': market, 'module': Module_name, 'operation': 'enqueue_bg'})
	else:
		chart1(market)
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
		market = data['orderbook']['market']
		maxv = data['orderbook']['data'][0][3]
		data['orderbook']['data'].insert(0, ['buy', 0, 0, maxv])
		ChartData_ob[market] = data['orderbook']['data']
		chart1(market)

	elif 'market_trades' in data:
		ChartData_trades[data['market_trades']['market']] = data['market_trades']['data']
		chart2(data['market_trades']['market'])

	elif 'analysis_wavetrend' in data:
		ChartData_analisis1[data['analysis_wavetrend']['market']] = data['analysis_wavetrend']['data']
		chart3(data['analysis_wavetrend']['market'])

	elif 'analysis_stoch_rsi' in data:
		ChartData_analisis2[data['analysis_stoch_rsi']['market']] = data['analysis_stoch_rsi']['data']
		chart4(data['analysis_stoch_rsi']['market'])

