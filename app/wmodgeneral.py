#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window, document

jq = window.jQuery
Module_name = "general"
Ws_comm = None

class datastore():
	def __init__(self):
		self.data = {'master_unlocked': False}

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


