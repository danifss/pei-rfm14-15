from Queue import *
from socket import *
from TrackAnalyser import *
from time import sleep

ip_addr = ([(s.connect(('8.8.8.8', 80)), \
            s.getsockname()[0], s.close()) \
            for s in [socket(AF_INET, \
            SOCK_DGRAM)]][0][1])


cameraId = 1
portTrack = 7777

th_trackAnalyser = TrackAnalyser(portTrack,100,10,cameraId)


th_trackAnalyser.start()

#sleep(100)

th_trackAnalyser.stop()
