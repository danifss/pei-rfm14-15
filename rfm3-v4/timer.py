import time
import threading

class timer(threading.Thread):
	def __init__(self, count):
		super(timer,self).__init__()
		self.count = count
		self.stop = False
	def run(self):
		while (self.count >= 0):
			self.count -= 1
			time.sleep(1)
		self.stop = True
	def end(self):
			return self.stop
