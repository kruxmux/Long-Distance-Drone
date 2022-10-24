import serial

arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=.1)

while True:
	data = arduino.readline()[:-2].split() #the last bit gets rid of the new-line chars
	if data:
		print "Roll: " + ch1 + " Throttle: " + ch2 + " Pitch: " + ch3 + " Yaw: " + ch4
