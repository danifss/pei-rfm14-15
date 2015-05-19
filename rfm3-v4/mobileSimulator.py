from socket import *
import time
import select
import random
import sys

# class to get char from stdin
class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

#port to listen for server
listen_port = 10100

#Discover server's ip address
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.bind(('',listen_port))
message = ''
print 'Finding server...'
while message != 'server':
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
tcp_s.send('mobile\n')

# wait for 'ready' message
message = ''
while message != 'ready\n':
    data = tcp_s.recv(128)
    message = data.split(':')[0]
    if message == 'error':
        tcp_s.close()
        print 'Error: '+data.split(':')[1]
        sys.exit(0)

print 'Everything ready'
a = raw_input('Press enter to start game')
tcp_s.send('start:helder\n')
print 'Game started'

commands_port = 4444

udp_s = socket(AF_INET, SOCK_DGRAM)
udp_s.bind((server_ip, 0))
udp_s.settimeout(2)
server_addr = (server_ip, commands_port)

getch = _GetchUnix()

end = False
while not end:
    a = getch()
    udp_s.sendto(a, server_addr)
    r, w, e = select.select((tcp_s,),(),(),0)
    if r:
        data = tcp_s.recv(10).rstrip().split(':')
        if data[0] == 'end':
            print 'Got time over signal. Score is: '+data[1]
            end = True

print 'Mobile: closing sockets'
udp_s.close()
tcp_s.close()
