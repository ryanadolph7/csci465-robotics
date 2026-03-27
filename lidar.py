import time
from adafruit_rplidar import RPLidar

# Update port for your system (e.g., '/dev/ttyUSB0' for Linux)
lidar = RPLidar(None, '/dev/ttyUSB0', timeout=3)

try:
    for scan in lidar.iter_scans():
        for (_, angle, distance) in scan:
            if(distance < 800):
                lidar.stop()
                lidar.disconnect()
                print("Too close at angle", angle)
                break
            print(f"Angle: {angle}, Distance: {distance}")
except KeyboardInterrupt:
    print('Stopping.')
finally:
    lidar.stop()
    lidar.disconnect()