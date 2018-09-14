#
# (c) 2017 elias/jashita
#
# BUBBLE-INVESTING
#
#

from browser import ajax
import json


class graph_orderbook:

	def __init__(self, name, objchart, axis_cb=None):
		self.name = name
		self.chart1 = objchart
		self.query_url = None
		self.market = ''
		self.data = None
		self.data_cb = None
		self.buy_data = None
		self.sell_data = None
		self.title = ''
		self.orders = []
		self.setoption_data = None
		self.axispointer_cb = axis_cb
		self.init()

	def init(self):
		print("graph_orderbook init")


	def tooltip(self, params, ticker, callback):
		#print("name  type   seriesname   value")
		#for p in params:
		#	print(p.name, p.componentType, p.seriesName, p.value)
		if self.axispointer_cb is not None:
			self.axispointer_cb(self.name, self.chart1, self.chart1.getOption())

	def load_data(self, dat):
		self.data = dat['data']
		self.buy_data = [[r[1], r[3]] for r in self.data if r[0]=='buy']
		self.sell_data = [[r[1], r[3]] for r in self.data if r[0]=='sell']

		maxY = max([x[3] for x in self.data])
		if self.title != "":
			self.chart1.setOption({"title": {"text": self.title, 'left': '20%', 'textStyle': {'color': '#aaa'}}})
		self.chart1.setOption({"grid": {"show": False, 'borderColor': '#f00', "top": "0", "left": "10", "right": "10"}})

		if 'datazoom' in dat:
			print("datazoom", dat['datazoom'])
			dz_pos = dat['datazoom']
		else:
			dz_pos = [0,100]

		self.chart1.setOption({"tooltip": {"trigger": 'axis', "axisPointer": {"type": 'cross', "show": True}, "formatter": self.tooltip, "alwaysShowContent": True}})

		self.chart1.setOption({
			"toolbox": {"show": True, "feature": {"saveAsImage": {}}},
			"xAxis": {"type": 'value',
					"splitLine": {"lineStyle": {"color": '#333', "width": 1}},
					"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
					"axisTick": {"lineStyle": {"color": "#aaa"}}},
			"yAxis": {"show": False,
					"splitLine": {"lineStyle": {"color": '#444', "width": 1}},
					"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
					"axisTick": {"lineStyle": {"color": "#aca"}}},
			"dataZoom": [{"type": "slider", "start": dz_pos[0], "end": dz_pos[1], "xAxisIndex": [0], "filterMode": 'filter'}],
			"responsive": True,
			"animation": False,
			"series":
				[{"id": "b",
					"name": "buy " + self.market, "data": self.buy_data,
						"type": 'line', "showSymbol": False,
				  		"lineStyle": {"color": 'rgba(100,200,100,1)'},
						"areaStyle": { "normal": {"color": {"type": 'linear', "x": 0, "y": 0, "x2": 0, "y2": 1,
									"colorStops": [{"offset": 0, "color": 'rgba(0,253,90, 1)'},
													{"offset": 0.5, "color": 'rgba(0,253,90,0.4)'},
													{"offset": 1, "color": 'rgba(0,253,90,0)'}]}}}
				},
				{"id": "s",
					"name": "sell " + self.market, "data": self.sell_data,
						"type": 'line', "showSymbol": False,
						 "lineStyle": {"color": 'rgba(200,100,100,1)'},
						 "areaStyle": { "normal": {"color": {"type": 'linear', "x": 0, "y": 0, "x2": 0, "y2": 1,
									"colorStops": [{"offset": 0, "color": 'rgba(253,100,78,0.8)'},
													{"offset": 0.5, "color": 'rgba(253,100,78,0.4)'},
													{"offset": 1, "color": 'rgba(253,100,78,0)'}]}}}
				}],
			"itemStyle": {"normal": {"color": '#999'}}
		})

		if len(self.orders) > 0:
			print("w_mod_graph", self.orders)
			dat = []
			for o in self.orders:
				if o[0] == 'buy':
					color = "#5baa25"
				else:
					color = "#f95155"
				if False:
					dat.append([{"name": "", "xAxis": o[1], "yAxis": 0, "symbol": "none",
								"lineStyle": {"normal": {'type': 'solid', 'color': color}}},
								{"name": "", "xAxis": o[1], "yAxis": maxY, "symbol": "none"}])
				dat.append({"xAxis": str(o[1]), "symbol": "none", "lineStyle": {"normal": {'type': 'solid', 'color': color}}})
			print('>>>>orders:', dat)
			self.chart1.setOption({"series": [{"name": "marks", "markLine": {"silent": True, "animation": False, "data": dat}}]})

			#dat.append({"yAxis": o[1], "symbol": "none", "lineStyle": {"normal": {'type': 'solid', 'color': color}}})
			#gdata["series"].append({"name": "marks", "type": "line", "markLine": {"data": dat}})



class graph_simple:

	def __init__(self, name, objchart, axis_cb=None):
		self.name = name
		self.chart1 = objchart
		self.market = ''
		self.data = None
		self.limits_x = None
		self.limits_y = None
		self.hard_limits_y = None
		self.title = ''
		self.setoption_data = None
		self.axispointer_cb = axis_cb
		self.init()

	def init(self):
		print("graph_simple init")


	def tooltip(self, params, ticker, callback):
		#print("name  type   seriesname   value")
		#for p in params:
		#	print(p.name, p.componentType, p.seriesName, p.value)
		if self.axispointer_cb is not None:
			self.axispointer_cb(self.name, self.chart1, self.chart1.getOption())


	def load_data(self, dat):
		self.data = dat['data']
		self.limits_x = [self.data[0][0], self.data[-1][0]]

		if self.hard_limits_y is not None:
			self.limits_y = self.hard_limits_y
		else:
			self.limits_y = [min(*[x[y] for x in self.data for y in range(1, 5) if x[y] is not None]),
							 max(*[x[y] for x in self.data for y in range(1, 5) if x[y] is not None])]

		if self.title != "":
			self.chart1.setOption({"title": {"text": self.title, 'left': '20%', 'textStyle': {'color': '#aaa'}},
								  "grid": {"show": False, 'borderColor': '#f00', "top": "30", "left": "40", "right": "10", "bottom": "20"}})
		else:
			self.chart1.setOption({"grid": {"show": False, 'borderColor': '#f00', "top": "0", "left": "40", "right": "10", "bottom": "20"}})

		self.chart1.setOption({"tooltip": {"trigger": 'axis', "axisPointer": {"type": 'cross', "show": True}, "formatter": self.tooltip, "alwaysShowContent": True}})

		self.chart1.setOption({"toolbox": {"show": True, "feature": {"saveAsImage": {}}},
			"xAxis": {"type": 'category',
					  "axisLine": {"show": True, "lineStyle": {"color": '#aaa', "width": 0.5}},
					  "data": [x[0] for x in self.data]},
			"yAxis": {"type": "value", "axisPointer": {"snap": True},
					  	"scale": True, "splitArea": {"show": False},
					  "min": self.limits_y[0], "max": self.limits_y[1],
					  "axisLabel": {'show': True, 'color': "#ececec"},
					   "splitLine": {"show": True, "lineStyle": {"color": "#555"}},
						"axisLine": {"show": False, "lineStyle": {"color": '#999', "width": 0.5}},
						  "axisTick": {"lineStyle": {"color": "#888", "width": 0.5}}},
			"responsive": True,
			"animation": False,
		"itemStyle": {"normal": {"color": '#999'}}
		})

		series_colors = ['#FDA', '#FC0', '#C83', '#B6A']
		series_name = dat['timelapse']
		series = []
		for sernum in range(0, len(series_name)):
			series.append({"id": "s"+str(sernum+1),	"name": series_name[sernum], "data": [x[sernum+1] for x in self.data], "smooth": False,
						"type": 'line', "showSymbol": False, "lineStyle": {"normal": {"color": series_colors[sernum], "width": 1}}})

		self.chart1.setOption({"series": series})


class OrderBook1(graph_orderbook):

	def __init__(self, name, objchart, axis_cb=None):
		super().__init__(name, objchart, axis_cb)



class MarketTrades1(graph_simple):
	#["2004-01-02",10452.74,10409.85,10367.41,10554.96,168890000]
	#date, open, close, lowest, highest

	def __init__(self, name, objchart, axis_cb=None):
		super().__init__(name, objchart, axis_cb)
		self.orders = []

	def load_data(self, dat):
		print("load_data")
		self.data = {'category_data': [x[0] for x in dat], 'volume_data': [x[5] for x in dat], 'data': [x[1:6] for x in dat]}
		#self.trades_data = [[d[0], d[1]] for d in dat]
		#self.limits_x = [dat[0][0], dat[-1][0]]
		#self.limits_y = [0, max(self.data[0][3], self.data[-1][3])]
		print("cat data", self.data['category_data'][:2])
		print("lenght", len(self.data['data']))

		gdata = {"tooltip": {"trigger": 'axis', "axisPointer": {"type": 'cross', "show": True}, "formatter": self.tooltip, "alwaysShowContent": True},
			"grid": {"show": False, 'borderColor': '#f00', "top": "0", "left": "40", "right": "10", "bottom": "20"},
			"toolbox": {"show": True, "feature": {"saveAsImage": {}}},
			"axisPointer": {'link': {'xAxisIndex': 'all'}, 'label': {'backgroundColor': '#ca5'}},
			"yAxis": [{"scale": True, "splitArea": {"show": False}, "axisLabel": {'show': True, 'color': "#ececec"},
						"splitLine": {"show": True, "lineStyle": {"color": "#555"}}},
				{"max": max(self.data['volume_data'])*3, "splitNumber": 2, "axisLabel": {"show": False},
					"axisLine": {"show": False, }, "axisTick": {"show": False}, "splitLine": {"show": False}}],
			"xAxis": [{"type": 'category', "data": self.data['category_data'], "scale": True, "boundaryGap": False,
						"min": 'dataMin', "max": 'dataMax',
						"splitLine": {"lineStyle": {"color": '#333', "width": 1}},
						"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
						"axisTick": {"lineStyle": {"color": "#aaa"}}}
					],
			"responsive": True,
			"animation": False,
			"series":  [{"name": 'ohlc', "type": 'candlestick', "data": self.data['data'],
						 	"yAxisIndex": 0,
							"itemStyle": {"normal": {"color": "#1a924b", "color0": "#8f4441", "borderColor": None,
							"borderColor0": None}}},
						{"name": "volume", "type": "bar", "data": self.data['volume_data'],
						 "yAxisIndex": 1,
						 "itemStyle": {"normal": {"color": "#5c5c5c"}}}]
			}

		if self.title != '':
			gdata['title'] = {"text": self.title, 'left': '0%', 'textStyle': {'color': '#aaa'}}
			gdata["grid"] =  {"show": False, 'borderColor': '#f00', "top": "20", "left": "40", "right": "10", "bottom": "20"}


		if len(self.orders) > 0:
			print("w_mod_graph orders 2", self.orders)
			omin = min([x[1] for x in self.orders])
			omax = max([x[1] for x in self.orders])
			#dmin = min([x[0] for x in self.data['data']])
			dmin = self.data['data'][0][0]
			for d in self.data['data']:
				if min(d[0], d[1], d[2], d[3]) < dmin:
					dmin = min(d[0], d[1], d[2], d[3])
			#dmax = max([x[0] for x in self.data['data']])
			dmax = self.data['data'][0][0]
			for d in self.data['data']:
				if max(d[0], d[1], d[2], d[3]) > dmax:
					dmax = max(d[0], d[1], d[2], d[3])
			gdata['yAxis'][0]['min'] = "dataMin"
			gdata['yAxis'][0]['max'] = "dataMax"

			dat = []
			for o in self.orders:
				print(o[1], dmin, dmax)
				if o[1] < dmin or o[1] > dmax:
					continue
				if o[0] == 'buy':
					color = "#5baa25"
				else:
					color = "#f95155"
				dat.append({"yAxis": str(o[1]), "symbol": "none", "lineStyle": {"normal": {'type': 'solid', 'color': color}}})
				print("order:", o)
			gdata["series"].append({"name": "ohlc", "type": "line", "markLine": {"data": dat}})

		self.chart1.setOption(gdata)




class SeriesSimple(graph_simple):

	def __init__(self, name, objchart, axis_cb=None):
		super().__init__(name, objchart, axis_cb)




class PieChart1(graph_orderbook):
	def __init__(self, objchart):
		super().__init__(objchart)

	def load_data(self, dat):
		dat = dat['data']
		data = [{"name": d, "value": round((dat[d][0] + dat[d][1]) * dat[d][2][0], 0)} for d in dat]
		data.sort(key=lambda x: x['value'], reverse=True)
		data = data[:5]

		gdata = {"tooltip": {"trigger": 'item', "formatter": "{a} <br/>{b}: {c} ({d}%)"},
				 "toolbox": {"show": True, "feature": {"saveAsImage": {}}},
				 "series": [{"name": 'Balances', "type":'pie', "radius": ['40%', '55%'],
								"center": ['50%', '50%'],
								"label": {"normal": {"formatter": '{b|{b}}{abg|}\n{hr|}\n {c}  {per|{d}%}  ',
													"backgroundColor": '#eee', "borderColor": '#aaa', "borderWidth": 1,
													"borderRadius": 4, "padding": [0, 7],
									"rich": {"a": {"color": '#999', "lineHeight": 22, "align": 'center'},
										"hr": {"borderColor": '#aaa', "width": '100%', "borderWidth": 0.5, "height": 0},
										"b": {"fontSize": 16, "lineHeight": 33},
										"per": {"color": '#eee', "backgroundColor": '#334455', "padding": [2, 4], "borderRadius": 2}}}},
								"data": data
							}
							]
						}

		self.chart1.setOption(gdata)


