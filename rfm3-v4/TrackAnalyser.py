from socket import *
import select
from threading import *
import cv2
import math
import numpy
import matplotlib.pyplot as plt
from Camera import *
from PIL import Image, ImageFilter, ImageOps
import sys, traceback
import gc
import timeit
import copy
import os
import time
sys.settrace


class TrackAnalyser(Thread):

    def __init__(self, port = 1234, rangeCoord = 40, sizeLastCoords = 10, cameraId = 0):
        super(TrackAnalyser, self).__init__()
        self.end = False
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind(('0.0.0.0', port))
        self.tcp_socket.listen(2) #numero de conexoes em simultaneo
        self.unity_socket, self.addr = (None, None)

        # camera variables
        self.rval = True
        self.cam = Camera(cameraId)
        self.lastCoords = [] # save last coords
        self.lastIO = [] #saves last in or out
        self.rangeCoord = rangeCoord # range parameter comparing with new coord
        self.sizeLastCoords = sizeLastCoords
        #variable to save initial position
        self.initialPoint = (None, None)

        #SaveCoords()
        #init position save
        for i in range(0, self.sizeLastCoords ):
            self.lastCoords.append((0,0)) # filling the initial coords
            self.lastIO.append((0)) #fill with out

        self.count = 0

        self.status = 1#auxiliar for lapCount
        self.lap = 1 # nr de voltas
        self.lapTime = []# tempos das voltas
        for i in range(0,10):
            self.lapTime.append(0)
        self.startL = 0# tempo de inicio de volta
        self.trackImage = 0#guarda a imagem
        self.elapsed=0#tempo de volta

        self.width = 0#image property
        self.height = 0#image property
        self.depth = 0#image property

    def run(self):
        #at the thread start moment de trackImage is loaded
        self.trackImage = cv2.imread("vect.jpg")
        self.height,self.width,self.depth = self.trackImage.shape
        #at the thread start moment, the car coords is initialized in this for-cycle
        for i in range(0, self.sizeLastCoords ):
            self.rval, frame = self.cam.get_frame() # get frame and rval
            circles = self.cam.get_circle(frame)
            if circles != None:
                for r in circles[0][:]:
                    x = r[0]
                    y = r[1]
                self.lastCoords[self.count]= (x,y) # filling the  coords
                self.count +=1
        self.sizeLastCoords = self.count  # size last coord is the number of well done initialization coords

        #comunication parameters
        self.initialPoint = (-1,-1)
        self.trackAdjust() # adjusting the track and settings
        state = "STOP"
        timeout = (0.1)
        self.unity_socket, self.addr = self.tcp_socket.accept()
        socket_list = [self.unity_socket]

        self.startL = time.time()
        #server connection loop
        while(not self.end):
            data = ""
            try:
                read_sockets = select.select(socket_list, [], [])[0]
                if len(read_sockets) == 0 and state == "STOP":
                    timeout = (0.1)
                    continue

                data = read_sockets[0].recv(4096)
                # self.tcp_socket.settimeout(0.1)

            except Exception, e:
                #self.tcp_socket.close()
                read_sockets[0].close()
                print "Error reading socket"
                print e
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
                break

            if data == "COORDS" or data == "COORDS\r\n":
                state = "COORDS"
                print 'Changed state to COORDS.'
            elif data == "TRACK" or data == "TRACK\r\n":
                state = "TRACK"
                print 'Changed state to TRACK.'
            elif data == "QUIT" or data == "QUIT\r\n":
                state = "STOP"
                print 'Changed state to STOP.'
            else:
                state = "STOP"
                continue

            if state == "COORDS":
                send = ""
                read_sockets[0].shutdown(SHUT_RD)
                ret = self.sendCoords()
                if ret == None or ret == "NO_COORDS":
                    send = "NO_COORDS"
                else:
                    retx,rety = ret
                    send += "COORDS:" + str(retx) + "," + str(rety)
                    io = "OUT"
                    io = self.inOrOut(ret)
                    send += ":POS:" + str(io)
                    send += ":LAP:" + str(self.lap)
                    self.elapsed = time.time()
                    self.elapsed -= self.startL
                    send += ":LAPTIME:" + str(self.elapsed)
                read_sockets[0].sendall(send)
                #read_sockets[0].shutdown(SHUT_WR)
                #read_sockets[0].close()
                #self.tcp_socket.close()


            if state == "TRACK":
                read_sockets[0].shutdown(SHUT_RD)
                self.sendTrack(read_sockets[0])
                #self.tcp_socket.close()
                #read_sockets[0].close()

            if state == "STOP":
                read_sockets[0].shutdown(SHUT_RD)
                self.tcp_socket.close()
                read_sockets[0].close()
                self.stop()

        total=0
        for i in range(0,10):
            total += self.lapTime[i]

        print "Race time="+ str(total)
        print 'Track Analyser Thread: Ended'

    def inOrOut(self,(x,y)):
        sumat = 0

        #call lapCount
        self.lapCount((x,y))

        for i in range (0, self.sizeLastCoords-1): # position shift of IN/OUT log
            self.lastIO[i] = self.lastIO[i+1]
            sumat += self.lastIO[i]

        if(x>=0 and y>=0 and x<= self.width and y <= self.height):
            #print self.trackImage[x][y]

            if( self.trackImage[x][y][0] <= 10 and self.trackImage[x][y][1] <= 10 and self.trackImage[x][y][2] <= 10):
                rt = "IN"
                self.lastIO[-1] = 1
            else:
                rt = "OUT"
                self.lastIO[-1] = 0

            ## Validacao
            if sumat < abs(self.sizeLastCoords/2) and rt == "IN": #ignore this time
                rt = "OUT"
            elif sumat >= abs(self.sizeLastCoords/2) and rt == "OUT":#ignore this time
                rt = "IN"
            return rt
        else:
            return "IOERR" #error if passed coords is out of bounds

    def sendCoords(self):
        #x,y = self.getCameraData() # remove and get a coord from queue
        #circles = self.getCameraData() # remove and get a coord from queue
        #self.rval = self.cam.rval
        ignoreCount = 0 # if lost the car position, after some iterations it will force new position
        self.rval, frame = self.cam.get_frame() # get frame and rval
        #frame = self.cam.crop_frame(frame) # crop frame
        # for i in range(0, self.sizeLastCoords):
        #     circles = self.cam.get_circle(frame)
        #     x = circles[0]
        #     y = circles[1]
        #     self.lastCoords[i]= (x,y) # filling the  coords
        circles = self.cam.get_circle(frame)
        if circles != None:
            for i in circles[0][:]:
                x = i[0]
                y = i[1]

                if(self.count < self.sizeLastCoords): # adding the first coords
                    self.lastCoords[self.count] = (x,y)
                    self.count += 1
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
                        return x,y
        else:
            return "NO_COORDS"

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

    def sendTrack(self,soc):
        image = open('transparente.png','rb')
        l = image.read(4096)
        while(l):
            soc.sendall(l)
            l = image.read(4096)
        image.close()

    def trackAdjust(self):
        notCorrect = True
        th = 100 # Representa o valor de threshold
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
            cv2.destroyWindow("Display window")

            image = Image.fromarray(im).convert('RGB')
            width = image.size[0]
            height = image.size[1]
            print width," ",height

            # Criar histograma para determinar valor de threshold entre pretos e brancos
            # histo = image.histogram()
            histo = image.convert('L').histogram()
            plt.plot(histo)
            plt.show()
            black_value = 0

            #th = 50 # Representa o valor de threshold
            print 'Threshold: ',th
            # Determinar um valor intermedio
            min_level =  sorted(histo)[2*len(histo)/ch]
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
            cv2.waitKey(20)

            try:
                print "Valor de threshold: "
                op = raw_input()
                if op != "done":
                    res = int(op)
                    print "Numero de divisao do histograma: "
                    op2 = raw_input()
                    res_ch = int(op2)
                    if res > 0:
                        th = res
                    if res_ch > 0:
                        ch = res_ch
                else:
                    break

                cv2.destroyWindow("Vector preview")
            except Exception, e:
                # th = 50
                # ch = 3
                print "Invalid values. Keeped last values th = " + str(th) + " ch = " + str(ch)
                cv2.destroyWindow("Vector preview")
                #break


        cv2.destroyWindow("Vector preview")

    def lapCount(self,(x,y)):
        (a,b) = self.initialPoint

        if((math.pow((x-a),2) + math.pow((y-b),2))<=20 and self.status==0):# if inside of circular range and previous coords are outside of the circle range then
            self.status=1# coords inside the range
            if lap <= 10:# if lap number is less than 10
                self.lapTime[lap-1]=self.elapsed #saves into the array
            self.lap +=1 #increment nr of laps
            self.elapsed=0# reset elapsed time
            self.startR=time.time()#reset race time
        else:
            self.status=0

