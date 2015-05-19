from threading import *
import cv2
import numpy

class Camera(object):
    ### init camera, rval and image shape
    def __init__(self, camera=0):
        self.cam = cv2.VideoCapture(camera)
        self.rval = False
        self.shape = None
        self.frame = None

        if self.cam.isOpened():
            rval,frame = self.cam.read()
            self.rval = rval
            self.shape = frame.shape
            self.frame = frame
        else:
            raise Exception("Camera not accessible")

    ### retorna leitura de uma frame da camera
    def get_frame(self):
        return self.cam.read()
        #return self.rval, self.frame

    ### retorna um tuplo (height, width, depth)
    def get_shape(self):
        return self.shape

    ### liberta a camera
    def release_cam(self):
        self.cam.release()

    ### retorna frame preto e branco com contornos (grayimg, countorsArray)
    def get_contors(self,frame):
        imgray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        ret,thresh = cv2.threshold(imgray,100,255,0)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(imgray, contours, -1, (0,255,0), 5) # all contorns
        return imgray,contours

    ### retorna imagem com ponto detetado e coordenadas do centro de massa do carro
    def get_circle(self,frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gaussb = cv2.GaussianBlur(gray,(9,9),0) 
        circles = cv2.HoughCircles(gray,cv2.cv.CV_HOUGH_GRADIENT,1,1000,param1=50,param2=30,minRadius=0,maxRadius=0)
        if circles != None:
            circles = numpy.uint16(numpy.around(circles))
        return circles

    ### draw circles on a frame
    def draw_circles(self, frame, circles):
        if circles != None:
            for i in circles[0,:]:
                # draw the outer circle
                cv2.circle(frame,(i[0],i[1]),i[2],(0,255,0),2)
                # draw the center of the circle
                cv2.circle(frame,(i[0],i[1]),2,(0,0,255),3) # i[0] and i[1] are the coordinates of the CM of the car
        return frame #, i[0],i[1]

    ### resize frame
    def resize_frame(self, frame, width, height):
        return cv2.resize(frame, (width,height))

    ### crop frame
    def crop_frame(self, frame):
        return frame[80:500,0:750]
        # NOTE: its img[y: y + h, x: x + w]

    ### showing the countors window
    def show_countors(self, frame):
        frame, countors = self.get_contors(frame)
        cv2.imshow("Contours",frame)
        cv2.waitKey(20)

    ### showing the detected circles
    def show_circles(self, frame):
        circles = self.get_circle(frame)
        frame = self.draw_circles(frame, circles)
        cv2.imshow("Circle",frame)
        cv2.waitKey(20)

    ### showing the countors with circles drawn
    def show_countorsCircle(self, frame):
        countorFrame,_ = self.get_contors(frame)
        circles = self.get_circle(frame)
        frame = self.draw_circles(countorFrame, circles)
        cv2.imshow("Countors with circles",frame)
        cv2.waitKey(20)


# cam = Camera()
# rval = cam.rval
# print rval , cam.shape
#
# while(rval):
#    rval, frame = cam.get_frame() # get frame and rval
#
#    #frame = cam.crop_frame(frame) # crop frame
#    #frame = cam.resize_frame(frame, 1024, 600) # resize frame
#
#    #cam.show_countors(frame)
#    cam.show_circles(frame)
#    #cam.show_countorsCircle(frame)
#
#
#    #dst = frame
#    #cv2.pyrUp( frame, frame, Size(tmp.cols*2, tmp.rows*2))
#
#
#    ch = cv2.waitKey(20)
#    if cv2.waitKey(1) & 0xFF == ord('q'):
#        break
#
#
# cam.release_cam()
# cv2.destroyAllWindows()
