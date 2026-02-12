import maestro
import time
servo = maestro.Controller()
userEntry = ""
servo.setAccel(1, 2)
servo.setAccel(2,2)
servo.setTarget(1, 6000)
servo.setTarget(2, 6000)
servo.setTarget(1, 4000)
servo.setTarget(2, 8000)
time.sleep(2)
servo.setTarget(1,6000)
servo.setTarget(2,6000)
servo.close()
