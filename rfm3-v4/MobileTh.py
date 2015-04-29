from socket import *
from threading import *
from time import *
from Queue import *

class Mobile(Thread):

	def __init__(self, dirsQueue, ipaddr, port):
		super(Mobile,self).__init__()
		self.end = False
		self.udp_socket = socket(AF_INET, SOCK_DGRAM)
		self.udp_socket.settimeout(1)
		self.udp_socket.bind((ipaddr, port))
		self.dirsQueue = dirsQueue

	def run(self):
		while (not self.end):
			try:
				data, addr = self.udp_socket.recvfrom(100)
				#print 'Mobile Thread  : Received command from mobile: %s' % data
				self.dirsQueue.put(data)
			except timeout:
				continue
		self.udp_socket.close()
		print 'Mobile Thread  : Ended'

	def stop(self):
		self.end = True