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

Module_name = "tradehistory"
Accounts = []
Account_active = 'All'
DataTables = {}

Last = {}

Ws_comm = None

def _get_info():
	Ws_comm.send({'call': 'account_tradehistory', 'module': Module_name, 'operation': 'enqueue'})
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
		if dif.seconds > 1:
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


def on_tabshown(ev):
	print("ev.target", ev.target.hash)



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


def _dt_0f(data, type, row, meta):
	return '{0:,.0f}'.format(data)

def _dt_8f(data, type, row, meta):
	return '{0:,.8f}'.format(data)


def datatable1_create(name='table1', cols, coldefs, dt_rows, precision=None):
	global DataTables

	if name in DataTables and DataTables[name] is not None:
		DataTables[name].clear()
		DataTables[name].destroy()

	# TODO: numeric alignment to the right doesn't work?
	DataTables[name] = jq('#'+name).DataTable({"data": dt_rows, "columns": [{'title': v} for v in cols],
							 "columnDefs": coldefs,
							 "order": [[1, "desc"]],
							 "dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
							 "lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
							 "buttons": [{"extend": 'copy', "className": 'btn-sm'},
										 {"extend": 'csv', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'pdf', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'print', "className": 'btn-sm'}]})



def incoming_data(data):
	global Last, Accounts
	import json
	Last.update(data)

	if 'settings_account_list' in data:
		Accounts = [x[0] for x in data['settings_account_list']]
		Accounts.insert(0, "All")
		print("account list", Accounts)
		create_account_selector(Accounts)

	if 'data' in data:
		lacc = "Account: <b>"+Account_active+"</b>"
		document['lAcc1'].innerHTML = lacc
		document['lAcc2'].innerHTML = lacc
		document['lAcc3'].innerHTML = lacc

		movs = json.loads(data['data'])
		if Account_active != 'All':
			movs = [x for x in movs if x[1]==Account_active]

		cols = ['Time', 'Account', 'Type', 'Pair', 'Price', 'Pays amount', 'Receives amount']
		coldefs = [{"targets": 4, "render": _dt_8f}, {"targets": [5, 6], "render": _dt_0f}, {"targets": 1, "visible": False, "searchable": False}]
		datatable1_create('table1', cols, coldefs, movs)

		cols = ['Time', 'Account', 'Type', 'Pair', 'Price', 'Pays amount', 'Receives amount']
		coldefs = [{"targets": 4, "render": _dt_8f}, {"targets": [5, 6], "render": _dt_0f}, {"targets": 1, "visible": False, "searchable": False}]
		datatable1_create('table2', cols, coldefs, [x for x in movs if x[2]=='BUY'])

		cols = ['Time', 'Account', 'Type', 'Pair', 'Price', 'Pays amount', 'Receives amount']
		coldefs = [{"targets": 4, "render": _dt_8f}, {"targets": [5, 6], "render": _dt_0f}, {"targets": 1, "visible": False, "searchable": False}]
		datatable1_create('table3', cols, coldefs, [x for x in movs if x[2]=='SELL'])
