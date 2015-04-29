from socket import *
import select
from threading import *
import cv2
import math
import numpy
from Camera import *
from PIL import Image, ImageFilter, ImageOps
import sys, traceback
import gc
import timeit
import copy
import os
import numpy as np
import matplotlib.pyplot as plt

sys.settrace

class TrackAnalyser(Thread):

    def __init__(self, port = 1234, rangeCoord = 100, sizeLastCoords = 10, cameraId = 0):
        super(TrackAnalyser,self).__init__()
        self.end = False
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind(('0.0.0.0', port))
        self.tcp_socket.listen(1)
        self.unity_socket, self.addr = (None, None)

        # camera variables
        self.rval = True
        self.cam = Camera(cameraId)
        self.lastCoords = [] # save last coords
        self.rangeCoord = rangeCoord # range parameter comparing with new coord
        self.sizeLastCoords = sizeLastCoords
        # variable to save initial position

        self.initialPoint = (None, None)

    def run(self):
        self.unity_socket, self.addr = self.tcp_socket.accept()
        socket_list = [self.unity_socket]
        state = "STOP"
        timeout = sys.maxint
        self.initialPoint = (-1,-1)
        self.trackAdjust() # adjusting the track and settings

        while(not self.end):
            data = ""

            try:
                read_sockets = select.select(socket_list, [], [], timeout)[0]
                if len(read_sockets) == 0 and state == "STOP":
                    timeout = sys.maxint
                    continue

                data = read_sockets[0].recv(4096)
            
            except Exception, e:
                print "Error reading socket"
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
                break

            if data == "COORDS":
                state = "COORDS"
                print 'Changed state to COORDS.'
            elif data == "TRACK":
                state = "TRACK"
                print 'Changed state to TRACK.'
            else:
                state = "STOP"
                continue

            if state == "COORDS":
                self.sendCoords()       
                self.tcp_socket.close()
            if state == "TRACK":
                self.sendTrack()
                self.tcp_socket.close()

        print 'Track Analyser Thread: Ended'

    def sendCoords(self):
        count = 0
        ignoreCount = 0 # if lost the car position, after some iterations it will force new position
        for i in range(0, self.sizeLastCoords):
            self.lastCoords.append((0,0)) # filling the initial coords

        #x,y = self.getCameraData() # remove and get a coord from queue
        #circles = self.getCameraData() # remove and get a coord from queue
        #self.rval = self.cam.rval
        self.rval, frame = self.cam.get_frame() # get frame and rval
        frame = self.cam.crop_frame(frame) # crop frame
        circles = self.cam.get_circle(frame)

        if circles != None:
            for i in circles[0][:]:
                x = i[0]
                y = i[1]

                if(count < self.sizeLastCoords): # adding the first coords
                    self.lastCoords[count] = (x,y)
                    count += 1
                else:
                    xm,ym = self.calcMediaLastCoords() # calculate mean of last coords
                    if(((x > xm+self.rangeCoord) or (x < xm-self.rangeCoord) or (y > ym+self.rangeCoord) or (y < ym-self.rangeCoord)) and ignoreCount < 50):
                        ignoreCount += 1
                        #continue # ignore new coord because it's away from the last ones
                    else:
                        ignoreCount = 0 # reset to zero
                        # shift left values of the array
                        for i in range (0, self.sizeLastCoords-1):
                            self.lastCoords[i] = self.lastCoords[i+1]

                        self.lastCoords[-1] = x,y # add new coord to last position on array

                        print x,y
                        if self.initialPoint == (-1,-1):
                            self.initialPoint = (x,y)
                        self.sendToUnity("Coords %d %d" % (x,y) ) # send coords to unity
        else:
            self.sendToUnity("NO_COORDS")

    #def getCameraData(self):
    #    self.rval = self.cam.rval
        
    #    self.rval, frame = self.cam.get_frame() # get frame and rval

    #    circles = self.cam.get_circle(frame)
    #    #if circles != None:
    #    return circles
    #    #else:
    #    #    return None

    #    #self.cam.show_countors(frame)
    #    #self.cam.show_circles(frame)
    #    #self.cam.show_countorsCircle(frame)
    #    #ch = cv2.waitKey(10)


    def stop(self):
        self.end = True
    
    def sendToUnity(self, data):
        try:
            self.unity_socket[0].sendall(data) # send coords do unity address
        except Exception, e:
            print "Error sending to unity"

    def calcMediaLastCoords(self):
        sumX = 0
        sumY = 0
        for i in range(0, self.sizeLastCoords):
            sumX += self.lastCoords[i][0] # sum all x
            sumY += self.lastCoords[i][1] # sum all y

        return sumX/self.sizeLastCoords, sumY/self.sizeLastCoords

    def sendTrack(self):
        image = Image.open("mascara.jpg")
        image.load()                                    # make sure PIL has read the data
        while True:
            size = os.stat('mascara.jpg').st_size       # get the size of the image
            buf = size                                  # keeps what you still have to send, like an image buffer
            lines = size                                # line size to send each time
            print 'Sending size'                        
            self.sendToUnity(str(size))                 # send size to the client
            print 'Sending...'
            #l = f.read(lines)
            bytes = 0                                   # bytes sent already
            while buf:
                print 'Sending...'
                if (buf < lines ):                      #if buf size is less than line size ...
                    l = image.read (buf)                    # read buf bytes
                    self.sendToUnity(l)                 # send bytes to client
                    bytes += buf                        # increment bytes sent
                    buf = 0                             # signals empty buffer
                else:
                    l = image.read(lines)                   # read line size bytes
                    self.sendToUnity(l)                 # send line size bytes
                    buf -= lines  # decrement buffer
                    bytes += lines

    def trackAdjust(self):
        notCorrect = True
        th = 50 # Representa o valor de threshold
        ch = 3
        while notCorrect: # enquanto a pista nao estiver corretamente vetorizada
            im = None
            # setting up track
            while self.rval:
                self.rval,im = self.cam.get_frame()
                im = self.cam.crop_frame(im) # crop frame
                #rval, image = vc.read()
                cv2.namedWindow( "Display window", cv2.CALIB_FIX_ASPECT_RATIO)
                cv2.imshow("Display window", im)
                #cv2.waitKey(20)
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break

            image = Image.fromarray(im).convert('RGB')
            width = image.size[0]
            height = image.size[1]
            print width," ",height

            # Criar histograma para determinar valor de threshold entre pretos e brancos
            histo = image.convert('L').histogram()
            plt.plot(histo)
            plt.show()
            black_value = 0
        
            #th = 50 # Representa o valor de threshold
            print 'Threshold: ',th
            # Determinar um valor intermedio
            min_level =  sorted(histo)[len(histo)/ch]
            while th < 255:
                if histo[th] > black_value:
                    black_value = histo[th]
                else:
                    if histo[th] < min_level:
                        break
                th = th+1
            print "Black Threshold: %d" % th
            # Isolar limites da pista
            mask = image.convert('L')
            mask = mask.point(lambda i: i < th and 255)
            maskPng = mask
            mask = mask.convert('RGB')
            mask.save("mask.jpg")

            # Transparencia
            output = ImageOps.fit(image,maskPng.size,centering=(50,50))
            output.putalpha(maskPng) # aplicar transparencia nos pontos pretos da mascara
            output.save('transparente.png')


            flooded = numpy.array(mask.copy())
            cv2mask = numpy.zeros((height+2, width+2), numpy.uint8)

            cv2.floodFill(flooded,cv2mask, (0,0), (255, 0, 0), (10,)*3, (10,)*3, cv2.FLOODFILL_FIXED_RANGE)
            cv2.floodFill(flooded,cv2mask, (width/2, height/2), (0, 255, 0), (10,)*3, (10,)*3, cv2.FLOODFILL_FIXED_RANGE)

            mask = Image.fromarray(flooded)

            mask.save("vect.jpg")
            print "Processing completed."

            # verificar se a vetorizacao foi correta
            vect = cv2.imread("vect.jpg")
            cv2.imshow('Vector preview',vect)
            cv2.waitKey(30)
            
            try:
                print "Valor de threshold: "
                op = raw_input()
                if op != "quit":
                    print "Numero de divisoes do histograma: "
                    oph = raw_input()
                    res = int(op)
                    resh = int(oph)
                    if res > 0 and resh > 0:
                        th = res
                        ch = resh
            except Exception, e:
                if op != "quit":
                    th = 50
                    ch =resh
                    print "Invalid threshold. Keeped default value TreshHold=" + str(th) + " and HistogramDivision= " + str(ch)
                else:
                    break
                #cv2.destroyWindow('Vector preview')
                continue
            finally:
                cv2.destroyWindow('Vector preview')


            #if 0xFF == ord('q'):
            #    notCorrect = False # vectorizacao finalizada
            #elif 0xFF == ord('o'): # aumentar threshold
            #    th = th + 10
            #elif 0xFF == ord('p'): # diminuir threshold
            #    th = th - 10 if th > 10 else 0
        
        #self.cam.release_cam()
        cv2.destroyAllWindows()

