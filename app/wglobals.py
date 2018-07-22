#
# (c) 2017 elias/vanissoft
#
#
#
#

from browser import timer

Timer1 = [None,None,None]

def dummy():
	pass

def set_timer(n, cb, secs):
	global Timer1
	Timer1[n] = timer.set_interval(cb, secs * 1000)

def clear_timer(n):
	global Timer1
	if Timer1[n] is not None:
		timer.clear_interval(Timer1[n])

def clear_timer_all():
	global Timer1
	for t in Timer1:
		if t is not None:
			timer.clear_interval(t)

