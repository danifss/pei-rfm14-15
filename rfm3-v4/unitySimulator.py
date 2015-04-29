from socket import *
from timer import *
import sys

game_time = 30 #seconds
listen_port = 10101

#Discover server's ip address
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.bind(('',listen_port))
message = ''
print 'Finding server...'
while message <> 'server':
	data, server_addr = s.recvfrom(512)
	message = data.split(':')[0]
server_ip = server_addr[0]
server_port = int(data.split(':')[1])

print 'Server found on: '+str(server_ip)
s.close()


#Connect to server
tcp_s = socket(AF_INET, SOCK_STREAM)
tcp_s.connect((server_ip,server_port))
print 'Connected to server.'
tcp_s.send('unity')

print 'Waiting for game to start...'
message = ['','']
while message[0] != 'start':
	data = tcp_s.recv(128)
	message = data.rstrip().split(':')
	if message[0] == 'error':
		tcp_s.close()
		print 'Error: '+message[1]
		sys.exit(0)

print 'Game started'
username = message[1]
print 'Username is: '+username
udp_s = socket(AF_INET, SOCK_DGRAM)
udp_s.bind(('', 6666))
udp_s.settimeout(2)


t = timer(game_time)
t.start()

while not t.end():
	try:
		data, addr = udp_s.recvfrom(100)
		print 'Unity : received: %s' % data.rstrip()
	except timeout:
		continue

print 'Unity : time over'
tcp_s.send('exit:10000\n')
udp_s.close()
tcp_s.close()