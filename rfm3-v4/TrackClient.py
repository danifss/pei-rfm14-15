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
                    reply = s.recv(4096)
                    print reply
                    sleep(1)
                except socket.error:
                    # Send failed
                    print 'Send failed\n\n'
                    # sys.exit(0)
        elif message == "TRACK":  # pedi a imagem
            try:
                s.send(message)
                print "Receiving..."
                f = open('imagemRecebida.png', 'wb')

                blockSize = geral.blockSize

                trackString = s.recv(blockSize)  # obter TRACK\n
                s.send('BoaCena')

                info = s.recv(blockSize)
                print info
                (tipo, w, h, size) = info.split(':')

                bytes = s.recv(blockSize)
                while bytes:
                    f.write(bytes)
                    bytes = s.recv(blockSize)
                    # print len(bytes)

                    sleep(0.2)
                    stdout.write('.')
                    stdout.flush()

                    # if bytes != "endOfImage":
                    #     break
                    if len(bytes) < blockSize:
                        f.write(bytes)
                        break


                # buf = int(s.recv(4096)) # get size
                # to_read = buf
                # bytes = 0
                # while buf > 0:
                #     if buf >= to_read:
                #         l = s.recv(to_read)
                #         f.write(l)
                #         buf -= to_read
                #         bytes += to_read
                #         #sleep(0.2)
                #         stdout.write('.')
                #         stdout.flush()
                #     else:
                #         l = s.recv(buf)
                #         f.write(l)
                #         bytes += buf
                #         buf = 0
                #         s.shutdown(SHUT_RD)

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


