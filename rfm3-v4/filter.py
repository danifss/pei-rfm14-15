
from PIL import Image, ImageFilter
import sys
import numpy
import gc
import timeit
import copy
import cv2
import time
sys.settrace
time.clock()

#image = Image.open(sys.argv[1])
image = Image.open("real.jpg")
width = image.size[0]
height = image.size[1]

# Criar histograma para determinar valor de threshold entre pretos e brancos
histo = image.histogram()
black_value = 0
th = 35 # Representa o valor de threshold
# Determinar um valor intermédio
min_level =  sorted(histo)[len(histo)/3] 
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
mask = mask.convert('RGB')

#mask.save(sys.argv[1].replace('.jpg','-clean.jpg'))

mask.save("barracaMask.jpg")


## Preenche usando um algoritmo básico
#def flood_fill(pixels, width, height, x, y, color):
#    pending =[ [x,y] ]

#    while len(pending) > 0:
#        pixel = pending[0]
#        if pixels[pixel[0], pixel[1]] != (0,0,0):
#            return
#        for N in pending:
#            if pixels[N[0], N[1]] != (0,0,0):
#                continue

#            w = N[0]
#            e = N[0]
#            while w < width-1 and pixels[w, N[1]] == (0, 0, 0):
#                w += 1

#            while e >= 1 and pixels[e, N[1]] == (0, 0, 0):
#                e -= 1

#            for n in xrange(e,w):
#                pixels[n, N[1]] = color
#                if N[1] >= 1 and pixels[n, N[1]-1] == (0, 0, 0):
#                    pending.append([n, N[1]-1])
#                if N[1] <= height-2 and pixels[n, N[1]+1] == (0, 0, 0):
#                    pending.append([n, N[1]+1])


#pixels = mask.load()
#time.clock()
#start= time.time()
#gc.disable()
## Fill a partir das bordas
#print "flood fill1:"
#flood_fill(pixels, width, height, 0, 0, (255,0, 0))
#elapsed = time.time() - start
#print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed) 
#start1= time.time()
##Fill a partir do centro
#print "flood fill2:"
#flood_fill(pixels, width, height, width/2, height/2, (0,255, 0))
#elapsed1 = time.time() - start1
#print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed1) 
#print "total time: %02d" %(elapsed + elapsed1)
#gc.enable()

##mask.save(sys.argv[1].replace('.jpg','-fill.jpg'))
#mask.save("barracaMask-fill.jpg")


start= time.time()

flooded = numpy.array(mask.copy())
cv2mask = numpy.zeros((height+2, width+2), numpy.uint8)

cv2.floodFill(flooded,cv2mask, (0,0), (255, 0, 0), (10,)*3, (10,)*3, cv2.FLOODFILL_FIXED_RANGE)
cv2.floodFill(flooded,cv2mask, (width/2, height/2), (0, 255, 0), (10,)*3, (10,)*3, cv2.FLOODFILL_FIXED_RANGE)

#flooded_small = cv2.resize(flooded, (1024,768))
#cv2.imshow('floodfill', flooded_small,)
#cv2.waitKey()

mask = Image.fromarray(flooded)

mask.save("barracaNew.jpg")
elapsed = time.time() - start
print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed) 