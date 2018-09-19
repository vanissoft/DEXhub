#
# (c) 2017 elias/vanissoft
#
#
#


# activate (init): ask for enqueued data first

from browser import window, document
import json
import wglobals

jq = window.jQuery

Module_name = "settings"
Accounts = []


BasePrio = {}
BasePrioButton = {}
LastBasePrio = 0

def load():
	wglobals.Ws_comm.send({'call': 'settings_prefs_bases', 'module': "settings", 'operation': 'enqueue'})
	wglobals.Ws_comm.send({'call': 'account_list', 'module': "settings", 'operation': 'enqueue'})
	wglobals.Ws_comm.send({'call': 'get_settings_misc', 'module': "settings", 'operation': 'enqueue'})

def init(params):
	#jq('#panel1').toggleClass('ld-loading')
	load()
	document["bNewAccount"].bind('click', click_new_account)
	document["bSave"].bind('click', click_save_account)
	document["bCancel"].bind('click', click_save_cancel)
	document["bSaveMisc"].bind('click', click_save_misc)
	document["bBasesReset"].bind('click', click_baseprio_reset)
	document["bBasesResetOrder"].bind('click', click_baseprio_resetorder)
	document["bBasesSave"].bind('click', click_baseprio_save)

def click_new_account(ev):
	# toggle form visible
	jq('#form1').toggleClass('hidden')

def click_save_misc(ev):
	print("save misc")
	dat = {'master_password': document['iMPpassphraseSet'].value}
	wglobals.Ws_comm.send({'call': 'save_misc_settings', 'data': dat, 'module': "settings", 'operation': 'enqueue'})


def click_save_account(ev):
	jq('#form1').addClass('hidden')
	dat = [document['iName'].value, document['iFamiliar'].value, document['iWifkey'].value]
	wglobals.Ws_comm.send({'call': 'account_new', 'data': dat, 'module': "settings", 'operation': 'enqueue'})

def click_save_cancel(ev):
	jq('#form1').addClass('hidden')

def click_del_account(ev):
	id = int(ev.target.id.split('_')[1])
	print("del account", id)
	wglobals.Ws_comm.send({'call': 'account_delete', 'id': id, 'module': "settings", 'operation': 'enqueue'})

def click_baseprio(ev):
	global LastBasePrio
	print(ev.target.id)
	print(BasePrioButton[ev.target.id])
	if BasePrio[BasePrioButton[ev.target.id]] == 0:
		LastBasePrio += 1
		BasePrio[BasePrioButton[ev.target.id]] = LastBasePrio
		document[ev.target.id].innerHTML = LastBasePrio


def click_baseprio_reset(ev):
	global BasePrio, BasePrioButton, LastBasePrio
	LastBasePrio = 0
	for b in BasePrioButton:
		if b in BasePrioButton and BasePrioButton[b] in BasePrio:
			BasePrio[BasePrioButton[b]] = 0
		if b in document:
			document[b].innerHTML = '?'

def click_baseprio_resetorder(ev):
	wglobals.Ws_comm.send({'call': 'settings_prefs_bases', 'orderbyops': 0, 'module': "settings", 'operation': 'enqueue'})

def click_baseprio_save(ev):
	print('click_baseprio_save')
	lbase = []
	for b in BasePrio:
		if BasePrio[b] == 0:
			BasePrio[b] = 9999
		lbase.append([b, BasePrio[b]])
		print(b, BasePrio[b])
	lbase.sort(key=lambda x: x[1])
	dat = [x[0] for x in lbase]
	print(dat[:10])
	wglobals.Ws_comm.send({'call': 'save_settings_bases', 'data': dat, 'module': "settings", 'operation': 'enqueue'})


def onResize():
	pass

def incoming_data(data):
	global Accounts, BasePrio, BasePrioButton, LastBasePrio
	print('module', Module_name, "incoming_data")
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


	elif 'settings_prefs_bases' in data:
		BasePrio = {}
		bases_list = data['settings_prefs_bases']

		document['table2'].clear()
		t1 = '<table class="table table-bordered table-hover"><thead><tr>' + \
			'<th>Base Token</th><th>Order</th>' + \
			'</tr></thead><tbody>'
		t2 = ''
		num = 0
		for base in bases_list:
			row = ''
			row += '<td>{}</td>'.format(base)
			row += '<td><button id="bPrioBase_{}" class="btn btn-accent btn-sm">{}</button></td>'.format(num, num+1)
			t2 += '<tr>{}</tr>'.format(row)
			BasePrio[base] = num+1
			BasePrioButton['bPrioBase_{}'.format(num)] = base
			num += 1
		LastBasePrio = num

		document['table2'].innerHTML = t1+t2+"</tbody></table>"
		for n in range(0, num):
			document["bPrioBase_{}".format(n)].bind('click', click_baseprio)

