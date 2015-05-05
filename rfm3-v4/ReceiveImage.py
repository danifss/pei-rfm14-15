import socket               # Import socket module
import cv2

s = socket.socket()         # Create a socket object
#host = '192.168.1.101'      # Get local machine name
host = socket.gethostname()
port = 7777                # Reserve a port for your service.
#s.bind((host, port))        # Bind to the port
remote_ip = socket.gethostbyname(host)
s.connect((remote_ip, port))


f = open('imagemRecebida.png','wb')
#s.listen(5)                 # Now wait for client connection.
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

    print "Receiving..."
    l = s.recv(999999)

    msg = l.split(':')
    fich = msg[0].split('=')[1]
    size = msg[1].split('=')[1]
    data = msg[2].split('=')[1]

    print fich
    print size

    f.write(data)

    #cv2.imshow("Imagem Recebida", f)
    #cv2.waitKey(100)

    f.close()

print "Done Receiving"
s.close()                # Close the connection
