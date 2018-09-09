#
# (c) 2017 elias/vanissoft
#
#
#
# TODO: ld-loading

from browser import window, document
import w_mod_graphs
from datetime import datetime

jq = window.jQuery

Module_name = "balances"
Accounts = []
Account_active = 'All'
Datatable_created = False
Dt1 = None

Last = {}

Ws_comm = None

def _get_info():
	Ws_comm.send({'call': 'get_balances', 'module': Module_name, 'operation': 'enqueue'})
	Last['time'] = datetime.now()

def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	Ws_comm.send({'call': 'account_list', 'module': Module_name, 'operation': 'enqueue'})

	if len(Last) == 0 or 'time' not in Last:
		_get_info()
	else:
		dif = datetime.now() - Last['time']
		if dif.seconds > 5*60:
			_get_info()
		else:
			incoming_data(Last)
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
	og.load_data({'data': data})


def on_tabshown(ev):
	print("ev.target", ev.target.hash)
	if ev.target.hash == "#tab-charts":
		pass
		#init_echart(Last['balances'])
		#ograph.resize()


def datatable_create(dt_rows, precision):
	global Datatable_created, Dt1
	cols = ['Asset', 'Total', 'Available', 'In Open Orders', 'Value in USD', '% of portfolio', 'Var % Over BTS']

	def dt_format(data, type, row, meta):
		tmpl = '{0:,.' + str(precision[row[0]]) + 'f}'
		return tmpl.format(data)

	if Dt1 is not None:
		Dt1.clear()
		Dt1.destroy()
	#if Datatable_created:
		#jq('#table2').DataTable().clear()
		#jq('#table2').DataTable().destroy()

	# TODO: numeric alignment to the right doesn't work?
	Dt1 = jq('#table2').DataTable({"data": dt_rows, "columns": [{'title': v} for v in cols],
							 "order": [[4, "desc"]],
							 "columnDefs": [{"targets": 1, "render": dt_format}, {"targets": 2, "render": dt_format},
											{"targets": 3, "render": dt_format}],
							 "dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
							 "lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
							 "buttons": [{"extend": 'copy', "className": 'btn-sm'},
										 {"extend": 'csv', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'pdf', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'print', "className": 'btn-sm'}]})
	Datatable_created = True

def click_change_account(ev):
	global Account_active
	for acc in Accounts:
		jq("#bAccount_" + acc).removeClass('btn-accent')
		jq("#bAccount_" + acc).addClass('btn-default')
	jq('#' + ev.target.id).removeClass('btn-default')
	jq('#' + ev.target.id).addClass('btn-accent')
	Account_active = ev.target.id[len('bAccount_'):]
	incoming_data(Last)


def create_account_selector(accs):
	if len(accs) == 0:
		return False
	btns = ""
	btns += '<button id="bAccount_{0}" class="btn btn-accent btn-sm">{0}</button>'.format(accs[0])
	for n in range(1, len(accs)):
		btns += '<button id="bAccount_{0}" class="btn btn-default btn-sm">{0}</button>'.format(accs[n])

	buttons = """<div class="buttons-margin">
					<p>Account selector.</p>
					<div>{}</div>
				</div>""".format(btns)
	document['account_selector'].innerHTML = buttons
	for acc in accs:
		document["bAccount_"+acc].bind('click', click_change_account)


def account_balances(data):
	bal0 = data['balances']
	print("account_balances", Account_active)
	if Account_active == "All":
		bal = {}
		for acc in bal0:
			for asset in bal0[acc]:
				print(acc,asset,bal0[acc][asset])
				if asset in bal:
					bal[asset][0] += bal0[acc][asset][0]
					bal[asset][1] += bal0[acc][asset][1]
				else:
					bal[asset] = bal0[acc][asset]
		return bal
	else:
		return bal0[Account_active]

def account_margin(data, asset='USD'):
	if asset == 'USD':
		lock = data['margin_lock_USD']
	else:
		lock = data['margin_lock_BTS']
	amount = 0
	print("margin_lock", lock)
	if Account_active == "All":
		for acc in lock:
			amount += lock[acc]
		return amount
	else:
		if Account_active in lock:
			return lock[Account_active]
		else:
			return 0


def incoming_data(data):
	global Last, Accounts

	Last.update(data)

	if 'settings_account_list' in data:
		Accounts = [x[0] for x in data['settings_account_list']]
		Accounts.insert(0, "All")
		print("account list", Accounts)
		create_account_selector(Accounts)

	if 'balances' in data:
		lacc = "Account: <b>"+Account_active+"</b>"
		document['lAcc1'].innerHTML = lacc
		document['lAcc2'].innerHTML = lacc
		document['lAcc3'].innerHTML = lacc
		balance = account_balances(data)
		Last = data
		init_echart(balance)
		total_base = 0
		# order by value in USD
		ord = []
		precision = {}
		for asset in balance:
			bal = balance[asset]
			total = (bal[0] + bal[1]) * bal[2][0]
			precision[asset] = bal[2][3]
			ord.append([asset, total])
			total_base += total
		ord.sort(key=lambda x: x[1], reverse=True)

		mlock = account_margin(data)
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
			bal = balance[asset]
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

