import time 
from adafruit_rplidar import RPLidar

# Update port for your system (e.g., '/dev/ttyUSB0' for Linux)
lidar = RPLidar(None, '/dev/ttyUSB0', timeout=3)
counter = 0
for scan in lidar.iter_scans():
    counter += 1
    print("New Scan " + str(counter))
    for (_, angle, distance) in scan:
        if((angle > 345) or (angle < 15)):
            #front detection
            if(distance < 400):
                print("Too close at the front")
        if((angle > 165) and (angle < 195)):
            #back detection
            if(distance < 400):
                print("Too close at the back")