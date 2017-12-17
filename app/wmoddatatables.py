#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document
from functools import partial

jq = window.jQuery

Module_name = "datatables"


def toggleloaders(ev):
	print(ev.target.id)
	if '1' in ev.target.id:
		jq('#panel1').toggleClass('ld-loading')
	elif '2' in ev.target.id:
		jq('#panel2').toggleClass('ld-loading')


def init():
	#incoming_data('')
	jq('#panel1').toggleClass('ld-loading')
	document['toggleLoaders1'].bind('click', toggleloaders)


	print(Module_name, "init")
	#window.DataTable.new(jq('#tableExample1'), {"dom": 't'})

	#jq('#tableExample1').DataTable({"dom": 't'})

	jq('#tableExample3').DataTable({"dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
		"lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
		"buttons": [{"extend": 'copy', "className": 'btn-sm'}, {"extend": 'csv', "title": 'ExampleFile', "className": 'btn-sm'},
			{"extend": 'pdf', "title": 'ExampleFile', "className": 'btn-sm'}, {"extend": 'print', "className": 'btn-sm'}]})


def onResize():
	pass

def incoming_data(data):
	# [market, 'sell', "{0:,.5f}".format(q1), "{0:,.8f}".format(q2 / q1), "{0:,.5f}".format(q2), t[1]]
	print('module', Module_name, "incoming_data")
	cols = "Market,Operation,Quantity,Price,Total,Date"
	dat1 = data['data']['open_positions']
	dat1.sort(key=lambda x: x[0]+x[3]+x[1])
	print(dat1[-2:])
	dat = []
	for d in dat1:
		tmpl1 = "{:,."+str(d[8])+"f}"
		tmpl2 = "{:,."+str(d[9])+"f}"
		dat.append([d[1]+"/"+d[3], d[0], tmpl1.format(d[2]), tmpl2.format(d[5]), tmpl2.format(d[6]), d[7]])
	jq('#tableExample1').DataTable({"data": dat, "columns": [{'title': v} for v in cols.split(",")],
		"dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
		"lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
		"buttons": [{"extend": 'copy', "className": 'btn-sm'},
					{"extend": 'csv', "title": 'ExampleFile', "className": 'btn-sm'},
					{"extend": 'pdf', "title": 'ExampleFile', "className": 'btn-sm'},
					{"extend": 'print', "className": 'btn-sm'}]})
	jq('#panel1').toggleClass('ld-loading')

