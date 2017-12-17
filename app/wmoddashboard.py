#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window
jq = window.jQuery

Module_name = "dashboard"

def sparklineCharts():
	jq(".sparkline").sparkline([20, 34, 43, 43, 35, 44, 32, 44, 52, 45],
		{'type': 'line', 'lineColor': '#FFFFFF', 'lineWidth': 3, 'fillColor': '#404652', 'height': 47, 'width': '100%'})

	jq(".sparkline7").sparkline([10, 34, 13, 33, 35, 24, 32, 24, 52, 35],
		{'type': 'line', 'lineColor': '#FFFFFF', 'lineWidth': 3, 'fillColor': '#f7af3e', 'height': 75, 'width': '100%'})

	jq(".sparkline1").sparkline([0, 6, 8, 3, 2, 4, 3, 4, 9, 5, 3, 4, 4, 5, 1, 6, 7, 15, 6, 4, 0],
		{'type': 'line', 'lineColor': '#2978BB', 'lineWidth': 3, 'fillColor': '#2978BB', 'height': 170, 'width': '100%'})

	jq(".sparkline3").sparkline(
		[-8, 2, 4, 3, 5, 4, 3, 5, 5, 6, 3, 9, 7, 3, 5, 6, 9, 5, 6, 7, 2, 3, 9, 6, 6, 7, 8, 10, 15, 16, 17, 15],
		{'type': 'line', 'lineColor': '#fff', 'lineWidth': 3, 'fillColor': '#393D47', 'height': 70, 'width': '100%'})

	jq(".sparkline5").sparkline([0, 6, 8, 3, 2, 4, 3, 4, 9, 5, 3, 4, 4, 5],
		{'type': 'line', 'lineColor': '#f7af3e', 'lineWidth': 2, 'fillColor': '#2F323B', 'height': 20, 'width': '100%'})

	jq(".sparkline6").sparkline([0, 1, 4, 2, 2, 4, 1, 4, 3, 2, 3, 4, 4, 2, 4, 2, 1, 3],
		{'type': 'bar', 'barColor': '#f7af3e', 'height': 20, 'width': '100%'})

	jq(".sparkline8").sparkline([4, 2], {'type': 'pie', 'sliceColors': ['#f7af3e', '#404652']})
	jq(".sparkline9").sparkline([3, 2], {'type': 'pie', 'sliceColors': ['#f7af3e', '#404652']})
	jq(".sparkline10").sparkline([4, 1], {'type': 'pie', 'sliceColors': ['#f7af3e', '#404652']})
	jq(".sparkline11").sparkline([1, 3], {'type': 'pie', 'sliceColors': ['#f7af3e', '#404652']})
	jq(".sparkline12").sparkline([3, 5], {'type': 'pie', 'sliceColors': ['#f7af3e', '#404652']})
	jq(".sparkline13").sparkline([6, 2], {'type': 'pie', 'sliceColors': ['#f7af3e', '#404652']})


def init():
	print("dashboard.init 1")

	# Flot charts data and options
	data1 = [[0, 16], [1, 24], [2, 11], [3, 7], [4, 10], [5, 15], [6, 24], [7, 30]]
	data2 = [[0, 26], [1, 44], [2, 31], [3, 27], [4, 36], [5, 46], [6, 56], [7, 66]]

	chartUsersOptions = {'series': {'splines': {'show': True, 'tension': 0.4, 'lineWidth': 1, 'fill': 1}},
		'grid': {'tickColor': "#404652", 'borderWidth': 0, 'borderColor': '#404652', 'color': '#404652'},
		'colors': ["#f7af3e", "#DE9536"]}

	jq.plot(jq("#flot-line-chart"), [data2, data1], chartUsersOptions)

	# Run toastr notification with Welcome message
	window.toastr.options = {"positionClass": "toast-top-right", "closeButton": 1, "progressBar": True, "showEasing": "swing", "timeOut": 6000}
	window.toastr.warning('<strong>Welcome to DEX HUB</strong> <br/><small>Have a profitable day. </small>')


	sparklineCharts()

def onResize():
	# TODO: to implement in main
	sparklineCharts()


def incoming_data(data):
	print("dashboard incoming:"+str(data['data']))
	document['lnum1'].innerHTML = str(int(data['data']*1000))