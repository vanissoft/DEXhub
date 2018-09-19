#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document
import json
jq = window.jQuery
Module_name = "general"

class datastore():
	def __init__(self):
		self.data = {'master_unlocked': False}
		self.status_list = []

Data = datastore()


def message(dat):
	print("message:", dat)
	if 'error' in dat and dat['error']:
		window.toastr.error(dat['message'], None,
			{"debug": 0, "newestOnTop": 1, "positionClass": "toast-top-right", "closeButton": 1, "progressBar": True})
	else:
		window.toastr.info(dat['message'], None,
			{"debug": 0, "newestOnTop": 1, "positionClass": "toast-top-right", "closeButton": 1, "progressBar": True})


def incoming_data(data):
	global Data
	#TODO:reload active module like settings? not reloading
	if 'master_unlock' in data:
		jq("#unlock_status").removeClass("pe-7s-lock")
		if not data['master_unlock']['error']:
			jq("#modal_master_password").modal("hide")
			document['MPerror'].innerHTML = ""
			jq("#unlock_status").addClass("pe-7s-unlock")
			Data.data['master_unlocked'] = True
		else:
			document['MPerror'].innerHTML = data['master_unlock']['message']
			jq("#unlock_status").addClass("pe-7s-lock")
			Data.data['master_unlocked'] = False
	elif 'status' in data:
		t = ''
		for q in ['operations', 'operations_bg']:
			if q in data['status']:
				for op in data['status'][q]:
					Data.status_list.append("<tr><td>{}</td><td>{}</td></tr>".format('operations', json.dumps(op)))
		for r in range(0, 5):
			if len(Data.status_list) == 0:
				break
			t += Data.status_list.pop(0)
		document['status_rows'].innerHTML = t

