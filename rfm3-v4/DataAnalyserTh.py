from socket import *
from threading import *
# from Queue import *
import traceback


class DataAnalyser(Thread):
    def __init__(self, dataQueue, unityAddr, mobile_sock, ipaddr='', port=0):
        super(DataAnalyser, self).__init__()
        self.end = False
        self.ignore = False
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.settimeout(2)
        self.udp_socket.bind((ipaddr, port))
        self.unityAddr = unityAddr
        self.dataQueue = dataQueue
        self.mobile_sock = mobile_sock

    def run(self):
        while not self.end:
            if not self.dataQueue.empty():
                x = self.dataQueue.get()
                # print 'Analyser Thread: Analysing data (' + x + ')'
                self.analyse(x)
        self.udp_socket.close()
        print 'Analyser Thread: Ended'

    def stop(self):
        self.end = True

    def sendToUnity(self, command):
        # print 'Analyser Thread: Sending command to unity: ' + command
        self.udp_socket.sendto(command, self.unityAddr)

    def analyse(self, data):  # TODO: analyse accelerometer data and send respective commands

        if not self.ignore:
            l = data.split('  ')
            # x = 0
            # y = 0
            # z = 0

            try:
                # x = l[0] / 100
                y = int(l[1]) / 100
                # z = l[2] / 100

                action = ''

                if y < -20:
                    action = 'Front_Collision'
                    print "Front Collision"

                # elif y > 20.0:
                # action = 'Back_Collision'
                # elif x > 60.0 or x < -60.0:
                # action = 'Lateral_Collision'
                # elif z > 20.0 or z < -15.0:
                # action = 'Jump'
                if action == 'Front_Collision' or action == 'Back_Collision' or action == 'Lateral_Collision':
                    self.mobile_sock.send('vibrate\n')
                if action != '':
                    print action
                    self.ignore = False
                self.sendToUnity(data + '  ' + action)
            # self.sendToUnity(data)
            except Exception:
                lol = True
            # , sys.exc_info()[0]
            #     print 'Exception in DataAnalyser (first is normal)', error
        else:
            self.ignore = False
