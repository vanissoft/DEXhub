#
# (c) 2017 elias/vanissoft
#
#
#
# TODO: ld-loading

from browser import window, document
import time
import w_mod_graphs

jq = window.jQuery

Module_name = "balances"
Accounts = []

Last = None

Ws_comm = None

def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	if Last is None:
		Ws_comm.send({'call': 'get_balances', 'module': Module_name, 'operation': 'enqueue'})
	else:
		Ws_comm.send({'call': 'letmeuselocalcache', 'module': Module_name, 'operation': 'enqueue'})
	#document["bRefresh"].bind('click', click_refresh)
	jq('.nav-tabs a').on('shown.bs.tab', on_tabshown)


def click_refresh(ev):
	Ws_comm.send({'call': 'get_balances', 'module': Module_name, 'operation': 'enqueue'})


def click_save_cancel(ev):
	jq('#form1').addClass('hidden')

def click_asset_detail(ev):
	print("asset detail not implemented")

def init_echart(data):
	jq("#echart1").show()
	ograph = window.echarts.init(document.getElementById("echart1"))
	og = w_mod_graphs.PieChart1(ograph)
	og.load_data(data)


def on_tabshown(ev):
	print("ev.target", ev.target.hash)
	if ev.target.hash == "#tab-charts":
		pass
		#init_echart(Last['balances'])
		#ograph.resize()


def datatable_create(dt_rows, precision):
	cols = ['Asset', 'Total', 'Available', 'In Open Orders', 'Value in USD', '% of portfolio', 'Var % Over BTS']

	def dt_format(data, type, row, meta):
		tmpl = '{0:,.' + str(precision[row[0]]) + 'f}'
		return tmpl.format(data)

	# TODO: numeric alignment to the right doesn't work?
	jq('#table2').DataTable({"data": dt_rows, "columns": [{'title': v} for v in cols],
							 "order": [[4, "desc"]],
							 "columnDefs": [{"targets": 1, "render": dt_format}, {"targets": 2, "render": dt_format},
											{"targets": 3, "render": dt_format}],
							 "dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
							 "lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
							 "buttons": [{"extend": 'copy', "className": 'btn-sm'},
										 {"extend": 'csv', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'pdf', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'print', "className": 'btn-sm'}]})


def incoming_data(data):
	global Last
	if 'uselocalcache' in data:
		data = Last
	if 'balances' in data:
		Last = data
		init_echart(Last['balances'])
		total_base = 0
		# order by value in USD
		ord = []
		precision = {}
		for asset in data['balances']:
			bal = data['balances'][asset]
			total = (bal[0] + bal[1]) * bal[2][0]
			precision[asset] = bal[2][3]
			ord.append([asset, total])
			total_base += total
		ord.sort(key=lambda x: x[1], reverse=True)

		mlock = data['margin_lock_USD']
		mlock_str = "{0:,.2f}".format(mlock)
		total_str = "{0:,.2f}".format(total_base)
		total2_str = "{0:,.2f}".format(total_base+mlock)
		document['table1'].clear()
		t1 = '<table class="table table-hover table-striped"><thead><tr>' + \
			'<th>Asset</th><th>Total</th><th>Available</th><th>In Open Orders</th><th>Value in USD<br>'+total_str+'$</th>' + \
		     '<th>% of portfolio</th><th>Change %<br>Over BTS</th>' + \
			'</tr></thead><tbody>'
		t2 = ''
		num = 0
		dt_rows = []
		for asset in [x[0] for x in ord]:
			bal = data['balances'][asset]
			row = ''
			row += '<td>{}</td>'.format(asset)
			row += '<td>{0:,.5f}</td>'.format(bal[0] + bal[1])
			row += '<td>{0:,.5f}</td>'.format(bal[0])
			row += '<td>{0:,.5f}</td>'.format(bal[1])

			value = (bal[0] + bal[1])*bal[2][0]
			if total_base == 0:
				porc = 0
			else:
				porc = value * 100 / total_base
			row += '<td>{0:,.2f}</td>'.format(value)
			row += '<td>{0:,.0f}%</td>'.format(porc)
			row += '<td>{0:,.2f}%</td>'.format(bal[2][2])
			t2 += '<tr>{}</tr>'.format(row)

			dt_rows.append([asset, bal[0] + bal[1], bal[0], bal[1], '{0:,.2f}'.format(value),
									'{0:,.0f}%'.format(porc), '{0:,.2f}%'.format(bal[2][2])])
			num += 1

		document['table1'].innerHTML = t1+t2+"</tbody></table>"
		if mlock == 0:
			document['lTotal'].innerHTML = total2_str+"$"
		else:
			document['lTotal'].innerHTML = total2_str+"$ (from which "+mlock_str+"$ locked as collateral)"

		datatable_create(dt_rows, precision)

