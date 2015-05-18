from TrackAnalyser import *
import geral
# from time import sleep

# ip_addr = ([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket(AF_INET, SOCK_DGRAM)]][0][1])

try:
    th_trackAnalyser = None
    cameraId = 0
    portTrack = 7777
    host = 'localhost'

    rangeCoord = 100
    sizeLastCoords = 10

    # th_clientTrackAnalyser = ClientTrackAnalyserTest(host, portTrack)
    th_trackAnalyser = TrackAnalyser(portTrack, rangeCoord, sizeLastCoords, cameraId)


    th_trackAnalyser.start()
    # th_clientTrackAnalyser.start()

    while th_trackAnalyser.isAlive():
        continue

    th_trackAnalyser.stop()
    # th_clientTrackAnalyser.stop()

except KeyboardInterrupt, e:
    print geral.carStat
    print e
    if th_trackAnalyser is not None:
        th_trackAnalyser.stop()
    sys.exit(0)
