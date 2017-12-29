#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document

jq = window.jQuery

Module_name = "balances"
Accounts = []

Ws_comm = None

def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	Ws_comm.send({'operation': 'enqueue', 'module': Module_name, 'what': 'get_balances'})
	#document["bRefresh"].bind('click', click_refresh)

def click_refresh(ev):
	Ws_comm.send({'operation': 'enqueue', 'module': Module_name, 'what': 'get_balances'})


def click_save_cancel(ev):
	jq('#form1').addClass('hidden')

def click_asset_detail(ev):
	print("asset detail not implemented")

def onResize():
	pass



def incoming_data(data):
	if 'balances' in data['data']:
		total_base = 0
		# order by value in USD
		ord = []
		for asset in data['data']['balances']:
			bal = data['data']['balances'][asset]
			total = (bal[0] + bal[1]) * bal[2][0]
			ord.append([asset, total])
			total_base += total
		ord.sort(key=lambda x: x[1], reverse=True)

		mlock = data['data']['margin_lock']
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
			bal = data['data']['balances'][asset]
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

			dt_rows.append([asset, '{0:,.5f}'.format(bal[0] + bal[1]), '{0:,.5f}'.format(bal[0]),
									'{0:,.5f}'.format(bal[1]), '{0:,.2f}'.format(value),
									'{0:,.0f}%'.format(porc), '{0:,.2f}%'.format(bal[2][2])])
			num += 1

		document['table1'].innerHTML = t1+t2+"</tbody></table>"
		document['lTotal'].innerHTML = total2_str+"$ ("+mlock_str+"$ locked as collateral)"

		cols = ['Asset', 'Total', 'Available', 'In Open Orders', 'Value in USD', '% of portfolio', 'Var % Over BTS']

		jq('#table2').DataTable({"data": dt_rows, "columns": [{'title': v} for v in cols],
			"order": [[4, "desc"]],
			"dom": "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>tp",
			"lengthMenu": [[10, 16, 50, -1], [10, 16, 50, "All"]],
			"buttons": [{"extend": 'copy', "className": 'btn-sm'},
						{"extend": 'csv', "title": 'Balances', "className": 'btn-sm'},
						{"extend": 'pdf', "title": 'Balances', "className": 'btn-sm'},
						{"extend": 'print', "className": 'btn-sm'}]})
