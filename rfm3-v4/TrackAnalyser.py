from Camera import *
from CarStatAnalyser import *
from socket import *
import select
from threading import *
import cv2
import math
import numpy
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter, ImageOps
import sys, traceback
import gc
import timeit
import copy
import os
import time
import geral
sys.settrace


class TrackAnalyser(Thread):

    def __init__(self, port = 1234, rangeCoord = 40, sizeLastCoords = 10, cameraId = 0):
        super(TrackAnalyser, self).__init__()
        self.end = False
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind(('0.0.0.0', port))
        self.tcp_socket.listen(2) #numero de conexoes em simultaneo
        self.unity_socket, self.addr = (None, None)

        # Thread para analisar stats do Carro
        self.th_carStatAnalyser = CarStatAnalyser(rangeCoord, sizeLastCoords, cameraId)

        # camera variables
        self.rval = False
        self.cam = None
        self.cameraId = cameraId
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

        self.status = 1 #auxiliar for lapCount
        self.lap = 1 # nr de voltas
        self.lapTime = [] # tempos das voltas
        for i in range(0,10):
            self.lapTime.append(0)
        self.startL = 0 # tempo de inicio de volta
        self.trackImage = 0 #guarda a imagem
        self.elapsed=0 #tempo de volta

        self.width = 0 #image property
        self.height = 0 #image property
        self.depth = 0 #image property

    def run(self):
        # #at the thread start moment the trackImage is loaded
        # self.trackImage = cv2.imread("vect.jpg")
        # self.height,self.width,self.depth = self.trackImage.shape

        #at the thread start moment, the car coords is initialized in this for-cycle
        # for i in range(0, self.sizeLastCoords ):
        #     self.rval, frame = self.cam.get_frame() # get frame and rval
        #     circles = self.cam.get_circle(frame)
        #     if circles != None:
        #         for r in circles[0][:]:
        #             x = r[0]
        #             y = r[1]
        #         self.lastCoords[self.count]= (x,y) # filling the  coords
        #         self.count +=1
        # self.sizeLastCoords = self.count  # size last coord is the number of well done initialization coords

        #comunication parameters
        self.initialPoint = (-1,-1)
        self.trackAdjust() # adjusting the track and settings
        state = "STOP"
        timeout = (0.1)

        socket_list = [self.tcp_socket]#inputs , socket we expect to read
        #socket_outputs_list = []#outputs we expect to write

        self.th_carStatAnalyser.start()
        # self.startL = time.time()
        #server connection loop
        while(not self.end):
            while socket_list:
                read_sockets = select.select(socket_list, [], [])[0]
                if len(read_sockets) == 0 and state == "STOP":
                    #timeout = (0.1)
                    continue
                count = -1
                for skt in read_sockets:
                    count +=1
                    if skt == self.tcp_socket:
                        client_socket = self.tcp_socket.accept()[0]#changed, only the connection
                        socket_list.append(client_socket)
                    else:
                        try:
                            self.handle_client_message(skt)

                        # self.tcp_socket.settimeout(0.1)

                        except Exception, e:
                            #self.tcp_socket.close()
                            skt.close()
                            del(socket_list[count])

                            print "Error reading socket"
                            print e
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
                            break


        total=0
        for i in range(0,10):
            total += self.lapTime[i]
        self.elapsed=time.time()
        self.elapsed-=self.startL
        total += self.elapsed
        print "Race time="+ str(total)
        print 'Track Analyser Thread: Ended'

    def handle_client_message(self, skt):
        data = skt.recv(4096)

        if data == "COORDS" or data == "COORDS\r\n":
            state = "COORDS"
            print 'Changed state to COORDS.'
        elif data == "TRACKSIZE" or data == "TRACKSIZE\r\n":
            state = "TRACKSIZE"
            print 'Changed state to TRACKSIZE.'
        elif data == "TRACK" or data == "TRACK\r\n":
            state = "TRACK"
            print 'Changed state to TRACK.'
        elif data == "QUIT" or data == "QUIT\r\n":
            state = "STOP"
            print 'Changed state to STOP.'
        else:
            state = "STOP"
            return False

        if state == "COORDS":
            send = ""
            skt.shutdown(SHUT_RD)
            # Ler a coordenada gerada da thread
            skt.sendall(geral.carStat)


        if state == "TRACK":
            skt.shutdown(SHUT_RD)
            self.sendTrack(skt)
            geral.camReady=1
            #self.tcp_socket.close()
            #read_sockets[0].close()
        if state == "TRACKSIZE":
            # skt.shutdown(SHUT_RD)
            self.sendTrackSize(skt)

        if state == "STOP":
            skt.shutdown(SHUT_RD)
            self.tcp_socket.close()
            skt.close()
            self.stop()


    def stop(self):
        self.end = True
        self.th_carStatAnalyser.stop()

    
    def sendToUnity(self, data):
        try:
            self.unity_socket[0].sendall(data) # send coords do unity address
        except Exception, e:
            print "Error sending to unity"


    def sendTrack(self,soc):
        image = open('transparente.png','rb')
        l = image.read(4096)
        while(l):
            soc.sendall(l)
            l = None
            l = image.read(4096)
        # soc.shutdown(SHUT_WR)
        # soc.sendall("endOfImage")
        image.close()


    def sendTrackSize(self,soc):
        size = str(os.path.getsize('transparente.png'))
        soc.sendall(size)
        soc.shutdown(SHUT_WR)


    def trackAdjust(self):
        notCorrect = True
        th = 100 # Representa o valor de threshold
        ch = 3
        cam = Camera(self.cameraId)
        rval = True
        while notCorrect: # enquanto a pista nao estiver corretamente vetorizada
            im = None
            # setting up track
            while rval:
                rval,im = cam.get_frame()
                #im = cam.crop_frame(im) # crop frame
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
            black_value = 0
            ## show histogram
            # plt.plot(histo)
            # plt.show()

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
            # print "Processing completed."

            # verificar se a vetorizacao foi correta
            vect = cv2.imread("vect.jpg")
            cv2.imshow("Vector preview",vect)
            cv2.waitKey(20)

            try:
                print "Change the threshold (enter done if ok): "
                op = raw_input()
                if op != "done":
                    res = int(op)
                    print "Number of divisions of the histogram (3 is normal): "
                    op2 = raw_input()
                    res_ch = int(op2)
                    if res > 0:
                        th = res
                    if res_ch > 0:
                        ch = res_ch
                else:
                    cv2.destroyWindow("Vector preview")
                    print "Waiting to send track..."
                    break

                cv2.destroyWindow("Vector preview")
            except Exception, e:
                # th = 50
                # ch = 3
                print "Invalid values. Keeped last values th = " + str(th) + " ch = " + str(ch)
                cv2.destroyWindow("Vector preview")
                #break


        cv2.destroyWindow("Vector preview")
        cam.release_cam()
        self.cam = None

