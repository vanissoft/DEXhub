#
# (c) 2017 elias/jashita
#
# BUBBLE-INVESTING
#
#

from browser import ajax
import json


class graph_orderbook:

	def __init__(self, objchart):
		self.chart1 = objchart
		self.query_url = None
		self.market = ''
		self.data = None
		self.data_cb = None
		self.buy_data = None
		self.sell_data = None
		self.q_callback = None
		self.limits_x = None
		self.limits_y = None
		self.zoom_back = []
		self.callbacks = {}
		self.title = ''
		self.orders = []
		self.setoption_data = None
		self.init()

	def init(self):
		choption = {"tooltip": {}, "title": {"text": self.title, 'left': '20%', 'textStyle': {'color': '#aaa'}},
					"grid": {"show": False, 'borderColor': '#f00', "top": "30", "bottom": "20", "left": "20", "right": "20"},
					"xAxis": {"type": 'value',
								"splitLine": {"lineStyle": {"color": '#333', "width": 1}},
								"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
								"axisTick": {"lineStyle": {"color": "#aaa"}}},
					"yAxis": {"show": False, "splitLine": {"lineStyle": {"color": '#444', "width": 1}},
								"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
								"axisTick": {"lineStyle": {"color": "#aca"}}},
					"series": [{"id": "b", "name": '1', "type": 'line', "data": [], "showSymbol": False},
								{"id": "s", "name": '2', "type": 'line', "data": [], "showSymbol": False}
								]}
		print("graph_orderbook init")


	def zoom(self):
		self.zoom_back.append([self.limits_x, self.limits_y])
		left = self.limits_x[0] + ((self.buy_data[-1][0] - self.limits_x[0]) / 1.5)
		right = self.limits_x[1] - ((self.limits_x[1] - self.sell_data[0][0]) / 1.5)
		self.limits_x = [left, right]
		self.limits_y = [0, int(self.limits_y[1]/3)]
		self.chart1.setOption({
			"xAxis": {"min": left, "max": right}})
		self.chart1.setOption({
			"yAxis": {"min": 0, "max": self.limits_y[1]}})

	def zoom_reset(self):
		if len(self.zoom_back) == 0:
			return
		else:
			zb = self.zoom_back.pop()
			if len(zb) == 0:
				self.limits_x = None
				self.limits_y = None
			else:
				self.limits_x = zb[0]
				self.limits_y = zb[1]
			self.chart1.setOption({
				"xAxis": {"min": self.limits_x[0], "max": self.limits_x[1]},
				"yAxis": {"min": 0, "max": self.limits_y[1]}})

	def load_data(self, dat):
		self.data = dat
		self.buy_data = [[r[1], r[3]] for r in self.data if r[0]=='buy']
		self.sell_data = [[r[1], r[3]] for r in self.data if r[0]=='sell']
		self.limits_x = [min(self.data[0][1], self.data[-1][1]),
							max(self.data[0][1], self.data[-1][1])]
		self.limits_y = [0, max(self.data[0][3], self.data[-1][3])]
		print("limits_y", self.limits_y)

		if self.title != "":
			self.chart1.setOption({"title": {"text": self.title, 'left': '20%', 'textStyle': {'color': '#aaa'}},
									"grid": {"show": False, 'borderColor': '#f00', "top": "30", "bottom": "20", "left": "10", "right": "15"}})
		else:
			self.chart1.setOption({"grid": {"show": False, 'borderColor': '#f00', "top": "0", "bottom": "20", "left": "10", "right": "15"}})

		self.chart1.setOption({"tooltip": {},
			"xAxis": {"min": None, "max": None, "type": 'value',
					"splitLine": {"lineStyle": {"color": '#333', "width": 1}},
					"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
					"axisTick": {"lineStyle": {"color": "#aaa"}}},
			"yAxis": {"min": self.limits_y[0], "max": self.limits_y[1], "show": False,
					"splitLine": {"lineStyle": {"color": '#444', "width": 1}},
					"axisLine": {"show": False, "lineStyle": {"color": '#aaa', "width": 1}},
					"axisTick": {"lineStyle": {"color": "#aca"}}},
			"responsive": True,
			"animation": False,
			"series":
				[{"id": "b",
					"name": "buy " + self.market, "data": self.buy_data,
						"type": 'line', "showSymbol": False,
						"areaStyle": { "normal": {"color": {"type": 'linear', "x": 0, "y": 0, "x2": 0, "y2": 1,
									"colorStops": [{"offset": 0, "color": 'rgba(0,253,90, 1)'},
													{"offset": 0.5, "color": 'rgba(0,253,90,0.4)'},
													{"offset": 1, "color": 'rgba(0,253,90,0)'}]}}}
				},
				{"id": "s",
					"name": "sell " + self.market, "data": self.sell_data,
						"type": 'line', "showSymbol": False,
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
				dat.append([{"name": "", "xAxis": o[1], "yAxis": 0, "symbol": "none",
							"lineStyle": {"normal": {'type': 'solid', 'color': color}}},
							{"name": "", "xAxis": o[1], "yAxis": self.limits_y[1] / 2, "symbol": "none"}])
			self.chart1.setOption({"series": [{"id": "b", "markLine": {"silent": True, "animation": False, "data": dat}}]})


class OrderBook1(graph_orderbook):

	def __init__(self, objchart):
		super().__init__(objchart)



class MarketTrades1(graph_orderbook):
	#["2004-01-02",10452.74,10409.85,10367.41,10554.96,168890000]
	#date, open, close, lowest, highest
	def __init__(self, objchart):
		super().__init__(objchart)

	def load_data(self, dat):
		print("load_data")
		self.data = {'category_data': [x[0] for x in dat], 'volume_data': [x[5] for x in dat], 'data': [x[1:6] for x in dat]}
		#self.trades_data = [[d[0], d[1]] for d in dat]
		#self.limits_x = [dat[0][0], dat[-1][0]]
		#self.limits_y = [0, max(self.data[0][3], self.data[-1][3])]
		print("cat data", self.data['category_data'][:2])
		print("lenght", len(self.data['data']))

		gdata = {"tooltip": {},
			"axisPointer": {'link': {'xAxisIndex': 'all'}, 'label': {'backgroundColor': '#ca5'}},
			"yAxis": [{"scale": True, "splitArea": {"show": False}, "axisLabel": {'show': True, 'color': "#ececec"},
				"splitLine": {"show": True, "lineStyle": {"color": "#555"}}},
				{"scale": True, "gridIndex": 1, "splitNumber": 2, "axisLabel": {"show": False},
					"axisLine": {"show": False, }, "axisTick": {"show": False}, "splitLine": {"show": False}}],
			"xAxis": [{"type": 'category', "data": self.data['category_data'], "scale": True, "boundaryGap": False,
						"axisLine": {"onZero": False}, "splitLine": {"show": False}, "splitNumber": 20,
						"min": 'dataMin', "max": 'dataMax', "axisPointer": {"z": 100}},
						{"type": 'category', "gridIndex": 1, "data": self.data['category_data'], "scale": True,
						"boundaryGap": True, "axisLine": {"onZero": False}, "axisTick": {"show": False},
						"splitLine": {"show": False}, "axisLabel": {"show": False}, "splitNumber": 20,
						"min": 'dataMin', "max": 'dataMax'}],
			"responsive": True,
			"animation": False,
			"series":  [{"name": 'Dow-Jones index', "type": 'candlestick', "data": self.data['data'],
							"itemStyle": {"normal": {"color": "#1a924b", "color0": "#8f4441", "borderColor": None,
							"borderColor0": None}}},
						{"name": "Volume", "type": "bar", "xAxisIndex": 1, "yAxisIndex": 1, "data": self.data['volume_data'],
						 "itemStyle": {"normal": {"color": "#5c5c5c"}}}]
			}

		if self.title == '':
			gdata['grid'] = [{'left': '10%', 'right': '5%', 'height': '65%', 'top': "10"},
										{'left': '10%', 'right': '5%', 'top': '80%', 'height': '16%'}]
		else:
			gdata['title'] = {"text": self.title, 'left': '0%', 'textStyle': {'color': '#aaa'}}
			gdata['grid'] = [{'left': '10%', 'right': '5%', 'height': '65%', 'top': "15"},
										{'left': '10%', 'right': '5%', 'top': '80%', 'height': '16%'}]

		if len(self.orders) > 0:
			print("w_mod_graph orders 2", self.orders)
			omin = min([x[1] for x in self.orders])
			omax = max([x[1] for x in self.orders])
			dmin = min([x[0] for x in self.data['data']])
			dmax = max([x[0] for x in self.data['data']])
			gdata['yAxis'][0]['min'] = "dataMin"
			gdata['yAxis'][0]['max'] = "dataMax"

			print(omin, dmin, "max:", omax, dmax)
			dat = []
			for o in self.orders:
				if o[1] < dmin or o[1] > dmax:
					continue
				if o[0] == 'buy':
					color = "#5baa25"
				else:
					color = "#f95155"
				dat.append({"yAxis": o[1], "symbol": "none", "lineStyle": {"normal": {'type': 'solid', 'color': color}}})
			gdata["series"].append({"name": "marks", "type": "line", "markLine": {"data": dat}})

		self.chart1.setOption(gdata)



class PieChart1(graph_orderbook):
	def __init__(self, objchart):
		super().__init__(objchart)

	def load_data(self, dat):
		data = [{"name": d, "value": round((dat[d][0] + dat[d][1]) * dat[d][2][0], 0)} for d in dat]
		data.sort(key=lambda x: x['value'], reverse=True)
		data = data[:5]

		gdata = {"tooltip": {"trigger": 'item', "formatter": "{a} <br/>{b}: {c} ({d}%)"},
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


