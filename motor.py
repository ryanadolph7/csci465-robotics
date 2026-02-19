import maestro
servo = maestro.Controller()

def leftWheel(amount):
    #ensures that a dangerous amount is not input to the servos.
    if(amount > 9000 or amount < 3000):
        return False
    servo.setAccel(1, 5)
    servo.setTarget(1, amount)
    return True


def rightWheel(amount):
    if (amount > 9000 or amount < 3000):
        return False
    servo.setAccel(2, 5)
    servo.setTarget(2, amount)
    return True

def headPan(amount):
    if (amount > 9000 or amount < 3000):
        return False
    servo.setAccel(3, 4)
    servo.setTarget(3, amount)
    return True

def headTilt(amount):
    if (amount > 9000 or amount < 3000):
        return False
    servo.setAccel(4, 4)
    servo.setTarget(4, amount)
    return True

def waistMovement(amount):
    if (amount > 9000 or amount < 3000):
        return False
    servo.setAccel(0,10)
    servo.setTarget(0, amount)
    return True

#Sets all servos to their resting position
def fullReset():
    for i in range(5):
        servo.setAccel(i,10)
        servo.setTarget(i, 6000)
