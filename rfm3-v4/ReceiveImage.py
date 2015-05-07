import socket               # Import socket module
import sys
from sys import stdout
from time import sleep
import cv2

s = socket.socket()         # Create a socket object
#host = '192.168.1.103'      # Get local machine name
host = socket.gethostname()
port = 7777                # Reserve a port for your service.
#s.bind((host, port))        # Bind to the port
remote_ip = socket.gethostbyname(host)
try:
    s.connect((remote_ip, port))
except socket.error:
    print "Error connecting to server."
    sys.exit(1)



#s.listen(5)                 # Now wait for client connection.
while True:
    #Send some data to remote server
    print "Message:"
    message = raw_input()
    try:
        if message == "COORDS": # pedi coords
            print "Num de coords:"
            iter = int(raw_input())
            for i in range(1, iter):
                s.send(message)
                reply = s.recv(4096)
                print reply
        else:
            s.send(message)
        print 'Mensagem enviada.\n\n'
    except socket.error:
        #Send failed
        print 'Send failed\n\n'
        #sys.exit(0)

    if message == "TRACK": # pedi a imagem
        try:
            print "Receiving..."
            f = open('imagemRecebida.png','wb')
            l = s.recv(4096)
            while(l):
                # stdout.write('.')
                # stdout.flush()
                # sleep(1)
                f.write(l)
                l = s.recv(4096)
            f.close()
            print 'Image received.'
        except socket.error:
            #Send failed
            print 'Send failed\n\n'
            #sys.exit(0)

    elif message == "quit":
        break

    # l = s.recv(999999)
    #
    # msg = l.split(':')
    # fich = msg[0].split('=')[1]
    # size = msg[1].split('=')[1]
    # data = msg[2].split('=')[1]

    # print fich
    # print size

    # f.write(data)

    # cv2.imshow("Imagem Recebida", f)
    # cv2.waitKey(100)


print "All done."
s.close()                # Close the connection
