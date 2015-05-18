# from socket import *
import socket
import sys
# from threading import *

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
    #host = '192.168.1.101'      # Get local machine name
    host = socket.gethostname()  # local machine
    port = 7777                  # Reserve a port for your service.
    remote_ip = socket.gethostbyname(host)
    s.connect((remote_ip, port))


    #f = open('imagemRecebida.png','wb')
    while True:
    #Send some data to remote server
        message = raw_input()
        try:
            s.send(message)
            print 'Mensagem enviada.'
        except socket.error:
            #Send failed
            print 'Send failed\n\n'
            #sys.exit(0)

        while True:
            try:
                print 'Try reading message from server.'
                reply = s.recv(1024)
                print reply
                if not reply:
                    break
            except socket.error:
                print 'Nothing was received.'
                #sys.exit(0)

    s.close()                # Close the connection
    #f.close()                   # Close the file
except KeyboardInterrupt, e:
    print e.message
    s.close()
    sys.exit(0)



#
#
# class ClientTrackAnalyserTest(Thread):
#     def __init__(self, host='localhost', port=7777):
#         super(ClientTrackAnalyserTest, self).__init__()
#         self.end = False
#         self.tcp_socket = socket(AF_INET, SOCK_STREAM)
#         self.host = host
#         self.port = port
#         self.remote_ip = '127.0.0.1' # socket.gethostbyname(self.host)
#         self.tcp_socket.connect((self.remote_ip, self.port))
#
#     def run(self):
#         while (not self.end):
#             # Send some data to remote server
#             message = raw_input()
#             try:
#                 self.tcp_socket.send(message)
#                 print 'Mensagem enviada.'
#             except socket.error:
#                 #Send failed
#                 print 'Send failed\n\n'
#                 sys.exit(0)
#
#             while True:
#                 try:
#                     print 'Try reading message from server.'
#                     reply = self.tcp_socket.recv(1024)
#                     print reply
#                     if not reply:
#                         break
#                 except socket.error:
#                     print 'Nothing was received.'
#                     self.stop()
#                     #sys.exit(0)
#
#     def stop(self):
#         self.tcp_socket.close()  # Close the connection
#         self.end = True;
