#
# (c) 2017 elias/vanissoft
#
#
#
# TODO: ld-loading

from browser import window, document
import w_mod_graphs

jq = window.jQuery

Module_name = "wmodtstats"

Ws_comm = None

Last = {}

def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	if len(Last) == 0:
		Ws_comm.send({'call': 'get_tradestats_token', 'module': Module_name, 'operation': 'enqueue'})
		Ws_comm.send({'call': 'get_tradestats_pair', 'module': Module_name, 'operation': 'enqueue'})
		Ws_comm.send({'call': 'get_tradestats_account', 'module': Module_name, 'operation': 'enqueue'})
		Ws_comm.send({'call': 'get_tradestats_accountpair', 'module': Module_name, 'operation': 'enqueue'})
	else:
		Ws_comm.send({'call': 'letmeuselocalcache', 'module': Module_name, 'operation': 'enqueue'})
	jq('.nav-tabs a').on('shown.bs.tab', on_tabshown)


def click_asset_detail(ev):
	print("asset detail not implemented")



def on_tabshown(ev):
	print("ev.target", ev.target.hash)

def _dt_format(data, type, row, meta):
	tmpl = '{0:,.0f}'
	return tmpl.format(data)


def datatable1_create(name='table1', cols, coldefs, dt_rows, precision=None):

	# TODO: numeric alignment to the right doesn't work?
	jq('#'+name).DataTable({"data": dt_rows, "columns": [{'title': v} for v in cols],
							 "columnDefs": coldefs,
							 "order": [[1, "desc"]],
							 "dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
							 "lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
							 "buttons": [{"extend": 'copy', "className": 'btn-sm'},
										 {"extend": 'csv', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'pdf', "title": 'Balances', "className": 'btn-sm'},
										 {"extend": 'print', "className": 'btn-sm'}]})


def incoming_data(data):
	import json
	global Last
	if 'uselocalcache' in data:
		data = Last
	if 'stats_token' in data:
		Last['stats_token'] = data['stats_token']
		cols = ['Asset', 'Ops', 'Volume', 'Ops /day', 'Volume /day']
		coldefs = [{"targets": 2, "render": _dt_format}, {"targets": 3, "render": _dt_format}, {"targets": 4, "render": _dt_format}]

		datatable1_create('table1', cols, coldefs, json.loads(data['stats_token']))
	if 'stats_pair' in data:
		Last['stats_pair'] = data['stats_pair']
		cols = ['Pair', 'Ops', 'Base amount', 'Quote amount', 'Price']
		coldefs = [{"targets": 1, "render": _dt_format}, {"targets": 2, "render": _dt_format}, {"targets": 3, "render": _dt_format},
					   {"targets": 4, "render": _dt_format}]
		datatable1_create('table2', cols, coldefs, json.loads(data['stats_pair']))
	if 'stats_account' in data:
		Last['stats_account'] = data['stats_account']
		cols = ['Account_id', 'Ops']
		coldefs = [{"targets": 1, "render": _dt_format}]
		datatable1_create('table3', cols, coldefs, json.loads(data['stats_account']))
	if 'stats_accountpair' in data:
		Last['stats_accountpair'] = data['stats_accountpair']
		cols = ['Account_id', 'Pair', 'Ops']
		coldefs = [{"targets": 2, "render": _dt_format}]
		datatable1_create('table4', cols, coldefs, json.loads(data['stats_accountpair']))
