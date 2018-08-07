#
# (c) 2017 elias/vanissoft
#
#
#


# activate (init): ask for enqueued data first

from browser import window, document

jq = window.jQuery

Module_name = "settings"
Accounts = []

Ws_comm = None

def load():
	Ws_comm.send({'call': 'account_list', 'module': "settings", 'operation': 'enqueue'})
	Ws_comm.send({'call': 'get_settings_misc', 'module': "settings", 'operation': 'enqueue'})

def init(comm):
	global Ws_comm
	Ws_comm = comm
	#jq('#panel1').toggleClass('ld-loading')
	load()
	document["bNewAccount"].bind('click', click_new_account)
	document["bSave"].bind('click', click_save_account)
	document["bCancel"].bind('click', click_save_cancel)

	document["bSaveMisc"].bind('click', click_save_misc)

def click_new_account(ev):
	# toggle form visible
	jq('#form1').toggleClass('hidden')

def click_save_misc(ev):
	print("save misc")
	dat = {'master_password': document['iMPpassphraseSet'].value}
	Ws_comm.send({'call': 'save_misc_settings', 'data': dat, 'module': "settings", 'operation': 'enqueue'})


def click_save_account(ev):
	jq('#form1').addClass('hidden')
	dat = [document['iName'].value, document['iFamiliar'].value, document['iWifkey'].value]
	Ws_comm.send({'call': 'account_new', 'data': dat, 'module': "settings", 'operation': 'enqueue'})

def click_save_cancel(ev):
	jq('#form1').addClass('hidden')

def click_del_account(ev):
	id = int(ev.target.id.split('_')[1])
	print("del account", id)
	Ws_comm.send({'call': 'account_delete', 'id': id, 'module': "settings", 'operation': 'enqueue'})


def onResize():
	pass

def incoming_data(data):
	global Accounts
	print('module', Module_name, "incoming_data")
	opt=''
	for x in range(0,10):
		opt+="<option>token {}</option>".format(x)
	document['lTokens'].innerHTML = opt
	if 'reload' in data:
		# don't reach here due to interception by wmodgeneral in wmain
		print("reload!!!!!!")
		load()
	elif 'settings_account_list' in data:
		Accounts = []
		if data['settings_account_list'] is None:
			return
		document['table1'].clear()
		t1 = '<table class="table table-bordered table-hover"><thead><tr>' + \
			'<th>Familiar name</th><th>Bitshares account</th><th>wif key</th><th>id</th><th>Operations</th>' + \
			'</tr></thead><tbody>'
		t2 = ''
		num = 0
		for r in data['settings_account_list']:
			row = ''
			for c in r:
				row += '<td>{}</td>'.format(c)
			Accounts.append(r)
			row += '<td><button id="bDelAccount_{}" class="btn btn-accent btn-sm">Delete</button></td>'.format(num)
			t2 += '<tr>{}</tr>'.format(row)
			num += 1

		document['table1'].innerHTML = t1+t2+"</tbody></table>"
		for n in range(0, num):
			document["bDelAccount_{}".format(n)].bind('click', click_del_account)


	elif 'settings_misc' in data:
		for k in data['settings_misc']:
			if k == 'master_password':
				document['iMPpassphraseSet'].value = ""
				document['lMPHash'].innerHTML = data['settings_misc'][k]


