from maestro import Controller
import time
servo = Controller()

left_l = 7000
left_r = 7000
right_l = 5000
right_r = 5000
forward_l = 4800
forward_r = 7200
back_l = 7200
back_r = 4800

def head_yes():
    servo.setAccel(4, 4)
    servo.setTarget(4, 4500)
    time.sleep(1)
    servo.setTarget(4, 7500)
    time.sleep(1)
    servo.setTarget(4, 6000)
    time.sleep(1)
    print("head_yes")

def head_no():
    servo.setAccel(3, 4)
    servo.setTarget(3, 4500)
    time.sleep(1)
    servo.setTarget(3, 7500)
    time.sleep(1)
    servo.setTarget(3, 6000)
    time.sleep(1)
    print("head_no")

def arm_raise():
    servo.setAccel(6, 4)
    servo.setTarget(6, 7500)
    time.sleep(1.5)
    servo.setTarget(6, 4500)
    time.sleep(1.5)
    servo.setTarget(6, 6000)
    time.sleep(1)
    print("arm_raise")

def dance90():
    servo.setAccel(1, 4)
    servo.setAccel(2, 4)
    servo.setTarget(1, 6000)
    servo.setTarget(2, 6000)
    time.sleep(1)
    servo.setTarget(1, left_l)
    servo.setTarget(2, left_r)
    time.sleep(1)
    servo.setTarget(1, right_l)
    servo.setTarget(2, right_r)
    time.sleep(1)
    servo.setTarget(1, 6000)
    servo.setTarget(2, 6000)
    print("dance90")


def main(): 
    head_yes()
    time.sleep(1)
    head_no()
    time.sleep(1)
    arm_raise()
    time.sleep(1)
    dance90()
    time.sleep(1)



if __name__ == "__main__":
    main()
