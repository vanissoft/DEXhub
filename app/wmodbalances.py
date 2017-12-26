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
	print('module', Module_name, "incoming_data")
	print('>', data['data'])
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
		total_str = "{0:,.2f}".format(total_base)
		document['table1'].clear()
		t1 = '<table class="table table-hover table-striped"><thead><tr>' + \
			'<th>Asset</th><th>Total</th><th>Available</th><th>In Open Orders</th><th>Value in USD<br>'+total_str+'$</th>' + \
		     '<th>Volume</th><th>Change %<br>Over BTS</th>' + \
			'</tr></thead><tbody>'
		t2 = ''
		num = 0
		for asset in [x[0] for x in ord]:
			bal = data['data']['balances'][asset]
			row = ''
			# [market, 'sell', "{0:,.5f}".format(q1), "{0:,.8f}".format(q2 / q1), "{0:,.5f}".format(q2), t[1]]
			row += '<td>{}</td>'.format(asset)
			row += '<td>{0:,.5f}</td>'.format(bal[0] + bal[1])
			row += '<td>{0:,.5f}</td>'.format(bal[0])
			row += '<td>{0:,.5f}</td>'.format(bal[1])
			row += '<td>{0:,.2f}</td>'.format((bal[0] + bal[1])*bal[2][0])
			row += '<td>{0:,.0f}</td>'.format(bal[2][1])
			row += '<td>{0:,.2f}%</td>'.format(bal[2][2])
			t2 += '<tr>{}</tr>'.format(row)
			num += 1

		document['table1'].innerHTML = t1+t2+"</tbody></table>"


