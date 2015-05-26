from threading import *
from Camera import *
import time
import math
import geral


class CarStatAnalyser(Thread):
    def __init__(self, rangeCoord = 40, sizeLastCoords = 10, cameraId = 0):
        super(CarStatAnalyser, self).__init__()
        self.end = False

        # camera variables
        self.rval = False
        self.cam = None
        self.cameraId = cameraId
        self.lastCoords = []  # save last coords
        self.lastIO = []  # saves last in or out
        self.rangeCoord = rangeCoord  # range parameter comparing with new coord
        self.sizeLastCoords = sizeLastCoords
        # variable to save initial position
        self.initialPoint = (-1, -1)

        self.status = 1  # auxiliar for lapCount
        self.lap = 1  # nr de voltas
        self.lapTime = []  # tempos das voltas

        self.startL = 0  # tempo de inicio de volta
        self.trackImage = None  # guarda a imagem
        self.elapsed = 0  # tempo de volta

        self.width = 0  # image property
        self.height = 0  # image property
        self.depth = 0  # image property

    def run(self):
        # init Camera
        self.cam = Camera(self.cameraId)

        # at the thread start moment the trackImage is loaded
        self.trackImage = cv2.imread(geral.VECTORNAME)
        self.height, self.width, self.depth = self.trackImage.shape

        # init position save
        for i in range(0, self.sizeLastCoords):
            self.lastCoords.append((0, 0))  # filling the initial coords
            self.lastIO.append(0)  # fill with out
        # init lap time
        for i in range(0, 10):
            self.lapTime.append(0)

        self.startL = time.time()

        count = 0
        ignoreCount = 0  # if lost the car position, after some iterations it will force new position

        while (not self.end):
            coord = None
            self.rval, frame = self.cam.get_frame()  # get frame and rval
            # self.cam.show_circles(frame)

            circles = self.cam.get_circle(frame)
            if circles != None:
                for i in circles[0][:]:
                    x = i[0]
                    y = i[1]

                    if count < self.sizeLastCoords:  # adding the first coords
                        self.lastCoords[count] = (x,y)
                        count += 1
                    else:
                        xm, ym = self.calcMediaLastCoords()  # calculate mean of last coords
                        if (((x > xm + self.rangeCoord) or (x < xm - self.rangeCoord) or (y > ym + self.rangeCoord) or (
                            y < ym - self.rangeCoord)) and ignoreCount < 50):
                            ignoreCount += 1
                            continue  # ignore new coord because it's away from the last ones
                        else:
                            ignoreCount = 0  # reset to zero
                            # shift left values of the array
                            for i in range(0, self.sizeLastCoords - 1):
                                self.lastCoords[i] = self.lastCoords[i + 1]

                            self.lastCoords[-1] = (x,y)  # add new coord to last position on array

                            if self.initialPoint == (-1, -1):  # just to save initial point
                                self.initialPoint = (x, y)

                            coord = x, y
            else:
                coord = "NO_COORDS"

            if coord == "NO_COORDS":  # No coords detected
                send = "NO_COORDS"
            elif coord is None:  # Coords out of range
                send = "OOR_ERR"
            else:  # Coords detected
                retx, rety = coord
                send = "COORDS:" + str(retx) + "," + str(rety)
                io = self.inOrOut((rety, retx))
                send += ":POS:" + str(io)
                send += ":LAP:" + str(self.lap)
                self.elapsed = time.time()
                self.elapsed -= self.startL
                send += ":LAPTIME:" + str(self.elapsed)
                geral.carStat = send

                # print send
                # time.sleep(0.1)
                # sys.stdout.write(send)
                # sys.stdout.flush()

    def stop(self):
        self.end = True

    def inOrOut(self, (x, y)):
        sumat = 0

        # lapCount
        self.lapCount((x, y))

        for i in range(0, self.sizeLastCoords - 1):  # position shift of IN/OUT log
            self.lastIO[i] = self.lastIO[i + 1]
            sumat += self.lastIO[i]

        if x >= 0 and y >= 0 and x <= self.height and y <= self.width:
            if self.trackImage[x][y][0] <= 10 and self.trackImage[x][y][1] <= 10 and self.trackImage[x][y][2] <= 10:
                rt = "IN"
                self.lastIO[-1] = 1
            else:
                rt = "OUT"
                self.lastIO[-1] = 0

            ## Validacao
            if sumat < abs(self.sizeLastCoords / 2) and rt == "IN":  # ignore this time
                rt = "OUT"
            elif sumat >= abs(self.sizeLastCoords / 2) and rt == "OUT":  # ignore this time
                rt = "IN"
            return rt
        else:
            return "IOERR"  # error if passed coords is out of bounds

    def calcMediaLastCoords(self):
        sumX = 0
        sumY = 0
        for i in range(0, self.sizeLastCoords):
            sumX += self.lastCoords[i][0]  # sum all x
            sumY += self.lastCoords[i][1]  # sum all y

        return sumX / self.sizeLastCoords, sumY / self.sizeLastCoords

    def lapCount(self, (x, y)):
        (a, b) = self.initialPoint

        if ((math.pow((x - a), 2) + math.pow((y - b),
                                             2)) <= 20 and self.status == 0):  # if inside of circular range and previous coords are outside of the circle range then
            self.status = 1  # coords inside the range
            if self.lap <= 10:  # if lap number is less than 10
                self.lapTime[self.lap - 1] = self.elapsed  # saves into the array
            self.lap += 1  # increment nr of laps
            self.elapsed = 0  # reset elapsed time
            self.startL = time.time()  # reset lap time
        else:
            self.status = 0
