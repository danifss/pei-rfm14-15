from threading import *
import cv2
import os
import math
import numpy
from Camera import *


class TrackData(Thread):
    def __init__(self, trackQueue, cameraId=0):
        super(TrackData, self).__init__()
        self.rval = True
        self.trackQueue = trackQueue
        self.cam = Camera(cameraId)

    def run(self):

        self.rval = self.cam.rval
        
        while self.rval:
            #self.rval, frame = vc.read()
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #gaussb = cv2.GaussianBlur(gray,(9,9),0)
            #circles = cv2.HoughCircles(gray,cv.CV_HOUGH_GRADIENT,1,1000,param1=50,param2=30,minRadius=0,maxRadius=0)
            #if circles != None:
            #    circles = numpy.uint16(numpy.around(circles))
            #    for i in circles[0,:]:
            #        ix = i[0]
            #        iy = i[1]
            #        # draw the outer circle
            #        cv2.circle(frame,(i[0],i[1]),i[2],(0,255,0),2)
            #        # draw the center of the circle
            #        cv2.circle(frame,(i[0],i[1]),2,(0,0,255),3)
            #        #self.trackQueue.put('('+ str(ix) +','+ str(iy) +')')
            #        self.trackQueue.put((ix,iy))
            #cv2.imshow("circles", frame)

            self.rval, frame = self.cam.get_frame() # get frame and rval

            circles = self.cam.get_circle(frame)
            if circles != None:
                for i in circles[0][:]:
                    ix = i[0]
                    iy = i[1]
                    self.trackQueue.put((ix,iy))

            #self.cam.show_countors(frame)
            self.cam.show_circles(frame)
            #self.cam.show_countorsCircle(frame)
            ch = cv2.waitKey(10)

        print 'Stop getting values!'

    def stop(self):
        self.rval = False
        cv2.destroyAllWindows()
