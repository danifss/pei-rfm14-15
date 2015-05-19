from TrackAnalyser import *
import geral
# from time import sleep


try:
    th_trackAnalyser = None
    cameraId = 0
    portTrack = 7777
    host = 'localhost'

    rangeCoord = 100
    sizeLastCoords = 10

    th_trackAnalyser = TrackAnalyser(portTrack, rangeCoord, sizeLastCoords, cameraId)

    th_trackAnalyser.start()

    while th_trackAnalyser.isAlive():
        continue

    th_trackAnalyser.stop()

except KeyboardInterrupt, e:
    print geral.carStat
    print e
    if th_trackAnalyser is not None:
        th_trackAnalyser.stop()
    sys.exit(0)
