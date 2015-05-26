import socket  # Import socket module
# from socket import *
import sys
from sys import stdout
from time import sleep
import cv2
import geral

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
    # host = '192.168.1.103'      # Get local machine name
    host = socket.gethostname()
    port = 7777  # Reserve a port for your service.
    # s.bind((host, port))       # Bind to the port
    remote_ip = socket.gethostbyname(host)
    try:
        s.connect((remote_ip, port))
    except socket.error:
        print "Error connecting to server."
        sys.exit(1)

    while True:
        # Send some data to remote server
        print "Message(quit to exit):"
        message = raw_input()

        if message == "COORDS":  # pedi coords
            print "Num de coords:"
            iter = int(raw_input())
            for i in range(1, iter):
                try:
                    s.send(message)
                    # print 'Mensagem enviada.'
                    coords = s.recv(4096)
                except socket.error:
                    print 'Send failed\n\n'
                print coords
                sleep(0.1)
        elif message == "TRACK":  # pedi a imagem
            try:
                s.send(message)
                print "Receiving..."
                f = open('imagemRecebida.png', 'wb')

                blockSize = geral.blockSize

                trackString = s.recv(blockSize)  # obter TRACK\n
                s.send('TRACK\n')

                info = s.recv(blockSize)
                print info
                (tipo, w, h, size) = info.split(':')

                count = 0
                bytes = s.recv(blockSize)
                while bytes:
                    f.write(bytes)
                    bytes = s.recv(blockSize)
                    # print len(bytes)

                    sys.stdout.write('\r[{0}] {1}%'.format('='*(count%100/10), count))
                    sys.stdout.flush()
                    # sleep(0.02)
                    count += 1

                    # if bytes != "endOfImage":
                    #     break
                    if len(bytes) < blockSize:
                        f.write(bytes)
                        break

                f.close()
                print 'Image received.'
            except socket.error:
                # Send failed
                print 'Send failed\n\n'
                # sys.exit(0)

        elif message == "quit":
            break


    print "All done."
    s.close()  # Close the connection
    sys.exit(0)

except KeyboardInterrupt, e:
    print e.message
    s.close()
    sys.exit(0)
except Exception, e:
    print e.message
    s.close()
    sys.exit(0)


def update_progress(progress):
    sys.stdout.write('\r[{0}] {1}%'.format('='*(progress/10), progress))
    sys.stdout.flush()
    time.sleep(0.02)


