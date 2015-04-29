import socket                # Import socket module
import sys

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
        sys.exit(0)

    while True:
        try:
            print 'Try reading message from server.'
            reply = s.recv(1024)
            print reply
            if not reply:
                break
        except socket.error:
            print 'Nothing was received.'
            sys.exit(0)

s.close()                # Close the connection
#f.close()                   # Close the file
