import maestro
import time
import sys
servo = maestro.Controller()
servo.setAccel(3,5)
i =1000* int( sys.argv[1])
print(i)
servo.setTarget(3,i)
time.sleep(1)
servo.setTarget(3,i-1000)
time.sleep(1)
servo.setTarget(3,i+1000)
servo.close()
