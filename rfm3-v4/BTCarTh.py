from bluetooth import *
from threading import *
# from time import *
# from Queue import *


class BTCar(Thread):

    def __init__(self, dirsQueue, dataQueue, accelerometerDataQueue, bd_addr, port):
        super(BTCar, self).__init__()
        self.end = False
        self.dirsQueue = dirsQueue
        self.dataQueue = dataQueue
        self.accelerometerDataQueue = accelerometerDataQueue
        self.bt_sock = BluetoothSocket(RFCOMM)
        self.bt_sock.connect((bd_addr, port))
        self.bt_sock.send('ba')
        self.bt_sock.send('p')

    def run(self):
        x = 's'
        l = 's'
        while not self.end:
            if not self.dirsQueue.empty():
                x = self.dirsQueue.queue[-1]
                self.dirsQueue.queue.clear()
                if (x == 'a' or x == 'd') and (l == 'q' or l == 'e' or l == 'z' or l == 'c' or l == 'w' or l == 'x'):
                    x = 's'
                    # print "BTCar Thread   : Sending command '" + x + "' to car"
                self.bt_sock.send(x)
                l = x
            s = self.readData()
            if len(s) > 3:
                # print "BTCar Thread   : Received accelerometer values: " + s
                self.dataQueue.put(s + '  ' + x)
                self.accelerometerDataQueue.put(s)
        print 'BTCar Thread   : Ended'

    def stop(self):
        self.end = True
        self.bt_sock.send('p')
        self.bt_sock.close()

    def readData(self):
        s = ""
        c = ''
        while c != '\n' and not self.end:
            c = self.bt_sock.recv(1)
            if c != '\r':
                s += str(c)
        return s.rstrip()