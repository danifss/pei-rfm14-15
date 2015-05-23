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

        #comunication parameters
        self.initialPoint = (-1,-1)
        self.trackAdjust() # adjusting the track and settings
        state = "STOP"
        timeout = (0.1)

        socket_list = [self.tcp_socket] # inputs , socket we expect to read
        #socket_outputs_list = [] # outputs we expect to write

        # Start car stats analyser thread
        self.th_carStatAnalyser.start()

        #server connection loop
        while(not self.end):
            while socket_list:
                read_sockets = select.select(socket_list, [], [])[0]
                if len(read_sockets) == 0 and state == "STOP":
                    #timeout = (0.1)
                    continue
                count = -1
                for skt in read_sockets: # tratar clientes ligados
                    count +=1
                    if skt == self.tcp_socket:
                        client_socket = self.tcp_socket.accept()[0] # [0] gives only the connection
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

        data = data.split('\r\n')[0]
        if data == "COORDS":
            state = "COORDS"
        elif data == "TRACK":
            state = "TRACK"
            print 'Changed state to TRACK.'
        elif data == "QUIT":
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


    def sendTrack(self, soc):
        image = open('transparente.png', 'rb')
        statinfo = os.stat('transparente.png')
        size = str(statinfo.st_size)
        w = '640'
        h = '480'

        soc.send('TRACK\n')
        # print str('PNG:'+w+':'+h+':'+size+'\n')
        info = 'PNG:'+w+':'+h+':'+size+'\n'
        soc.send(info) # ('PNG:%d:%d:%d\n' % w % h % size)
        # count = 0

        blockSize = geral.blockSize
        total = statinfo.st_size # image size
        while True:
            if total > blockSize:
                data = image.read(blockSize)
                total = total - blockSize #+ len(data)
            else:
                data = image.read(total)
                total = 0

            self.update_progress(1/total)
            sleep(1)

            print total
            if len(data) > 0:
                soc.send(data)
                if total == 0:
                    break
            else:
                break

        image.close()

        # soc.shutdown(SHUT_WR)
        # soc.sendall("endOfImage")

    def update_progress(progress):
        print '\r[{0}] {1}%'.format('#'*(progress/10), progress)

    def trackAdjust(self):
        notCorrect = True
        th = 100 # Representa o valor de threshold
        ch = 3
        cam = Camera(self.cameraId)
        rval = True
        while notCorrect: # enquanto a pista nao estiver corretamente vetorizada
            im = None
            # take photo of the track
            while rval:
                rval,im = cam.get_frame()
                # cv2.namedWindow("Display window", cv2.CALIB_FIX_ASPECT_RATIO)
                cv2.imshow("Display window", im)
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
            cv2.destroyWindow("Display window")

            image = Image.fromarray(im).convert('RGB')
            width = image.size[0]
            height = image.size[1]
            # print width," ",height

            # Criar histograma para determinar valor de threshold entre pretos e brancos
            # histo = image.histogram()
            histo = image.convert('L').histogram()
            black_value = 0
            ## show histogram
            # plt.plot(histo)
            # plt.show()

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
            mask.save(geral.MASKNAME)

            # Transparencia
            output = ImageOps.fit(image,maskPng.size,centering=(50,50))
            output.putalpha(maskPng) # aplicar transparencia nos pontos pretos da mascara
            output.save(geral.TRANSPARENTNAME)


            flooded = numpy.array(mask.copy())
            cv2mask = numpy.zeros((height+2, width+2), numpy.uint8)

            cv2.floodFill(flooded,cv2mask, (0,0), (255, 0, 0), (10,)*3, (10,)*3, cv2.FLOODFILL_FIXED_RANGE)
            cv2.floodFill(flooded,cv2mask, (width/2, height/2), (0, 255, 0), (10,)*3, (10,)*3, cv2.FLOODFILL_FIXED_RANGE)

            mask = Image.fromarray(flooded)
            mask.save(geral.VECTORNAME)

            # verificar se a vetorizacao foi correta
            vect = cv2.imread(geral.VECTORNAME)
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
