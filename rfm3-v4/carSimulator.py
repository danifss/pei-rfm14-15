from serial import *
import random
from timer import *

game_time = 30 # seconds
serial_port = '/dev/pts/3'

ser = Serial(serial_port, 115200, timeout = 1)

ser.flushInput()
ser.flushOutput()

t = timer(game_time)
t.start()
while not t.end():
    s = "%0.2f"%random.uniform(-2.5, 2.5) + " " + "%0.2f"%random.uniform(-2.5, 2.5) + " " + "%0.2f"%random.uniform(-2.5, 2.5)
    ser.write(s+"\n")
    print "Car   : received " + ser.read()

ser.flushOutput()
ser.flushInput()
