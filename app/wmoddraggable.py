#
# (c) 2017 elias/vanissoft
#
#
#

from browser import window
from functools import partial

jq = window.jQuery



def init():
	jq('.draggable-container [class*=col]').sortable({"handle": ".panel-body", "connectWith": "[class*=col]", "tolerance": 'pointer', "forcePlaceholderSize": True,
		"opacity": 0.8}).disableSelection()



def onResize():
	pass