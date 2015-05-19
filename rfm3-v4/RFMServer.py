from Queue import *
from socket import *
from DataAnalyserTh import *
from BTCarTh import *
from MobileTh import *
from TrackAnalyser import *
import sys, traceback
import time
import geral

ip_addr = ([(s.connect(('8.8.8.8', 80)), \
            s.getsockname()[0], s.close()) \
            for s in [socket(AF_INET, \
            SOCK_DGRAM)]][0][1])

#ip_addr = '127.0.0.1'

#GLOBAL VARIABLES
cameraId = 1
dataCollect = False
trackCollect = False
announcing_port_unity = 10101
announcing_port_mobile = 10100
unity_port = 6666
unity_portTrack = 7777
#unity_portITrack = 8888 #porta de envio de imagem da pista
commands_port = 4444
car_mac_addr = '98:D3:31:B0:81:26'
car_port = 1
mobile_sock = None
unity_sock = None
#car_mac_addr = '50:01:BB:77:A6:F9'
#car_port = 6

#Queues to hold values
dataQueue = Queue()
dirsQueue = Queue()
accelerometerDataQueue = Queue()
posQueue = Queue()                          #hold track car pos values

#TCP socket for control messages
TCPsock = socket(AF_INET, SOCK_STREAM)
TCPsock.bind(("0.0.0.0", 0))
tcp_port = TCPsock.getsockname()[1]
TCPsock.listen(2)
TCPsock.settimeout(3)

#UDP socket for broadcast announcing
UDPsock = socket(AF_INET, SOCK_DGRAM)
UDPsock.bind((ip_addr, 0))
UDPsock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
try:
    th_track = TrackAnalyser(unity_portTrack, cameraId=cameraId)
    th_track.start()
    while geral.camReady == 0:
        sleep(1)

    # Assert everything is connected
    unity = False
    mobile = False
    UDPsock.sendto('server:'+str(tcp_port)+":"+str(unity_portTrack),('<broadcast>',announcing_port_unity))
    UDPsock.sendto('server:'+str(tcp_port),('<broadcast>',announcing_port_mobile))
    while (not unity) or (not mobile):
        if not unity and not mobile:
            print 'Waiting for mobile and unity...'
        elif unity:
            print 'Waiting for mobile...'
        else:
            print 'Waiting for unity...'
        try:
            client_s, client_addr = TCPsock.accept()
            data = client_s.recv(128).rstrip()
            if data == 'unity':
                unity_sock = client_s
                unity_addr = client_addr
                unity = True
                print 'Got connected with unity on: '+client_addr[0]+','+str(client_addr[1])
            if data == 'mobile':
                mobile_sock = client_s
                mobile_addr = client_addr
                mobile = True
                print 'Got connected with mobile on: '+client_addr[0]+','+str(client_addr[1])
        except Exception:
            if not unity and not mobile:
                UDPsock.sendto('server:'+str(tcp_port)+":"+str(unity_portTrack),('<broadcast>',announcing_port_unity))
                UDPsock.sendto('server:'+str(tcp_port)+":"+str(unity_portTrack),('<broadcast>',announcing_port_mobile))
            elif unity:
                UDPsock.sendto('server:'+str(tcp_port)+":"+str(unity_portTrack),('<broadcast>',announcing_port_mobile))
            else:
                UDPsock.sendto('server:'+str(tcp_port)+":"+str(unity_portTrack),('<broadcast>',announcing_port_unity))

    end = False
    first_time = True
    #Threads
    while not end:
        try:

            th_btcar = BTCar(dirsQueue, dataQueue, accelerometerDataQueue, car_mac_addr, car_port)
            print 'Got connected with car'

            th_data_analyser = DataAnalyser(dataQueue, (unity_addr[0], unity_port), mobile_sock, ipaddr = ip_addr)

            th_mobile = Mobile(dirsQueue, '', commands_port)

            #Start all threads
            th_mobile.start()
            th_btcar.start()
            th_data_analyser.start()
            break
        except Exception, e:
            print e
            if th_btcar.isAlive():
                th_btcar.stop()

            if th_track.isAlive():
                th_track.stop()

            if th_mobile.isAlive():
                th_mobile.stop()

            if th_data_analyser.isAlive():
                th_data_analyser.stop()

            print 'Cant connect to car'
            mobile_sock.send('error:Server could not connect to the car\n')
            unity_sock.send('error:Server could not connect to the car\n')
            mobile_sock.close()
            unity_sock.close()
            client_s.close()

            #TCPsock.close()
            #sys.exit(0)


    while True:
        print 'Waiting for game to start...'

        if first_time:
            mobile_sock.send('ready\n')
            first_time = False


        ### GameModes types
        # start/end:1P:player
        # start/end:2P:player1:player2
        # start/end:free:player
        message = ['', '', '']
        while message[0] != 'start' and message[0] != 'end':
            try:
                message = mobile_sock.recv(512).rstrip().split(':')
            except timeout:
                print 'Waiting for game to start...'

        if message[0] == 'end':
            end = True
            break


        ## Filtering game modes
        if message[1] == '2P':
            unity_sock.send('start:2P:'+message[2]+':'+message[3]+'\n')
            geral.gameMode = message[1]
            if not th_track.isAlive(): # starting trackAnalyser thread
                th_track.start()
        elif message[1] == 'free':
            unity_sock.send('start:free:'+message[2]+'\n')
            geral.gameMode = message[1]
            if th_track.isAlive(): # stopping trackAnalyser thread
                th_track.stop()
        else: # 1P
            unity_sock.send('start:'+message[1]+'\n')
            geral.gameMode = "1P"
            if not th_track.isAlive(): # starting trackAnalyser thread
                th_track.start()

        print 'Game started'

        #Socket to get exit signal from unity
        score = ''
        unity_sock.settimeout(1)
        mobile_sock.settimeout(1)
        #Wait for exit signal from Unity
        ########## PLAYING
        while True:
            try:
                data = mobile_sock.recv(10).rstrip().split(':')
                if data[0] == 'exit':
                    print 'Terminated by mobile'
                    unity_sock.send('restart\n')
                    break

                unity_sock.send(data[0])
                print data

            except timeout:
                try:
                    data = unity_sock.recv(10).rstrip().split(':')
                    if data[0] == 'exit':
                        stop = True
                        mobile_sock.send('end:'+score+'\n')
                except timeout:
                    continue

        ## send restart signal and jump to se start threads if restart was pressed on mobile
        time.sleep(2)
except KeyboardInterrupt:

    #Stop all threads
    print 'Main Thread     : Stopping all threads'
    th_btcar.stop()
    th_mobile.stop()
    th_data_analyser.stop()
    th_track.stop()

    unity_sock.send('end\n')
    #Close sockets
    print 'Main Thread     : Closing sockets'
    mobile_sock.close()
    unity_sock.close()
    client_s.close()
    TCPsock.close()
    print 'Main Thread      : All done'
    sys.exit(0)

time.sleep(2)

if dataCollect:
    print 'Save accelerometer data to file.'
    fname = raw_input('File name: ')
    f = open(fname, 'w')
    while not accelerometerDataQueue.empty():
        f.write(accelerometerDataQueue.get()+'\n')
    f.close()
    print 'Data saved to file sucessfuly'

