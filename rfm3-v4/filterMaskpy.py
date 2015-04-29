import numpy as np
import argparse
import cv2
import Image
import time
#vc = cv2.VideoCapture(0)
#if vc.isOpened():
#	rval, image = vc.read()
#else:
#	rval = False

# load the image
image = cv2.imread("real.jpg")

#find all the 'black' shapes in the image
lower = np.array([0, 0, 0])
upper = np.array([30, 30, 30])
shapeMask = cv2.inRange(image, lower, upper)

#find the contours in the mask
(cnts, _) = cv2.findContours(shapeMask.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
print "I found %d black shapes" % (len(cnts))

# aplicar dilatacao
# aplicar erosao
#??

(altura,comprimento,_)= image.shape
start= time.time()
time.clock()
print "startVectoring 0%"
# pixel search, only right and up , the given search must get the closest white point in the mask image
#minx=0
#seq=0

for y in range(0,comprimento):
	minbr=0
	coloring= False
	seq=0
	for x in range(0,altura):
		#print minbr
		if shapeMask[x,y] == 255:# and shapeMask[x,y,1] == 255 and shapeMask[x,y,2] == 255:
			minbr += 1
			coloring = False
			continue
		else:
			if minbr > 5:
				coloring = True
				seq += 1

			if coloring == True and seq % 2 != 0:
				minbr = 0
				shapeMask[x,y]=100
				#shapeMask[x,y]=100
				#shapeMask[x,y]=100
			else:
				minbr = 0
print "Vectoring 50%"
for x in range(0,altura):
	minbr=0
	coloring= False
	seq=0
	for y in range(0,comprimento):
		#print minbr
		if shapeMask[x,y] == 255:# and shapeMask[x,y,1] == 255 and shapeMask[x,y,2] == 255:
			minbr += 1
			coloring = False
			continue
		else:
			if minbr > 5:
				coloring = True
				seq += 1

			if coloring == True and seq % 2 != 0:
				minbr = 0
				shapeMask[x,y]=100
				shapeMask[x,y]=100
				shapeMask[x,y]=100
			else:
				minbr = 0
print "100 %"
print "Vectoring Sucessfuly"
elapsed = time.time() - start
print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed) 
time.sleep(1)
cv2.namedWindow( "Mask", cv2.CALIB_FIX_ASPECT_RATIO);
cv2.imshow("Mask", shapeMask)
cv2.waitKey(0)



## loop over the contours
#for c in cnts:
#	# draw the contour and show it
#	cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
#	cv2.imshow("Image", image)
#	cv2.waitKey(0)
	
#def whiteNum(val,cim,x,y):
#	maxx=x + 50;
#	minx= x - 50;
#	maxy=y + 50;
#	miny= y - 50;

#	for r in range(minx,maxx):
#		for b in range(miny,maxy):
#			if()
#	return False
