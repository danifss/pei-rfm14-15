import socket
import sys
import geral

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
# host = '192.168.1.101'
host = socket.gethostname()
port = 7777  # Reserve a port for your service.
remote_ip = socket.gethostbyname(host)
try:
    s.connect((remote_ip, port))
except socket.error:
    print 'Error connecting to server.'
    sys.exit(1)


try:
    s.send('TRACK')
    f = open('imagemRecebida.png', 'wb')

    blockSize = geral.blockSize

    trackString = s.recv(blockSize)  # obter TRACK\n

    info = s.recv(blockSize)
    # print info
    (tipo, w, h, size) = info.split(':')

    bytes = s.recv(blockSize)
    while bytes:
        f.write(bytes)
        bytes = s.recv(blockSize)

        if len(bytes) < blockSize:
            f.write(bytes)
            break

    f.close()
    print 'ImageReceived.'
except socket.error:
    # Send failed
    print 'SendFailed\n\n'
    sys.exit(0)
except KeyboardInterrupt, e:
    print e.message
    s.close()
    sys.exit(0)
except Exception, e:
    print e.message
    s.close()
    sys.exit(0)
