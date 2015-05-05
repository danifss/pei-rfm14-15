# from Queue import *
# from socket import *
from TrackAnalyser import *
# from ClientTrackAnalyserTest import *
from time import sleep

# ip_addr = ([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket(AF_INET, SOCK_DGRAM)]][0][1])

try:
    cameraId = 0
    portTrack = 7777
    host = 'localhost'

    # th_clientTrackAnalyser = ClientTrackAnalyserTest(host, portTrack)
    th_trackAnalyser = TrackAnalyser(portTrack,100,3,cameraId)


    th_trackAnalyser.start()
    # th_clientTrackAnalyser.start()

    sleep(3600)

    th_trackAnalyser.stop()
    # th_clientTrackAnalyser.stop()
except KeyboardInterrupt, e:
    print e.message
    th_trackAnalyser.stop()
    sys.exit(0)
