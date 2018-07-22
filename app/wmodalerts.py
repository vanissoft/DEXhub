#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window
from functools import partial

jq = window.jQuery



def init():
	# TODO: not running, use a brython aproximation

	window.toastr.options = {"debug": False, "newestOnTop": False, "positionClass": "toast-bottom-right", "closeButton": "True", "progressBar": "1"}

	def alert(type, msg):
		if type == 'info':
			window.toastr.info(msg)
		elif type == 'success':
			window.toastr.success(msg)
		elif type == 'warning':
			window.toastr.warning(msg)
		elif type == 'error':
			window.toastr.error(msg)

	f1 = partial(alert, 'info', 'info')
	jq('.homerDemo1').on('click', f1)
	jq('.homerDemo2').on('click', window.toastr.success('Success - This is a LUNA success notification'))
	jq('.homerDemo3').on('click', window.toastr.warning('Warning - This is a LUNA warning notification'))
	jq('.homerDemo4').on('click', window.toastr.error('Error - This is a LUNA error notification'))


def onResize():
	pass