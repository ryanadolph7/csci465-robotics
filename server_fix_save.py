import random
import string
import sys
import time

from flask import Flask, render_template, request, jsonify
from maestro import Controller
app = Flask(__name__)
import os
import math
import dialogueParser
import action_functions
import motor
from adafruit_rplidar import RPLidar
import threading


DETECTION_DISTANCE_MM = 400     # comes out to about 7 inches
FRONT_MIN_ANGLE = 335
FRONT_MAX_ANGLE = 26
BACK_MIN_ANGLE = 155
BACK_MAX_ANGLE = 205
STOP_PWM = 6000


detection = {
    "forwardThing": False,
    "backwardThing": False
}

motion_state = {
    "y": 0.0,          # latest commanded forward/backward value from joystick
    "x": 0.0,          # latest commanded turning value from joystick
    "stopped_by_lidar": False
}

last_reported = {
    "front": False,
    "back": False
}

state_lock = threading.Lock()


def stop_drive():
    motor.leftWheel(STOP_PWM)
    motor.rightWheel(STOP_PWM)


def restart_lidar(lidar):
    try:
        lidar.stop()
        lidar.stop_motor()
    except:
        pass

    time.sleep(0.5)

    try:
        lidar.disconnect()
    except:
        pass

    time.sleep(0.5)

    lidar.connect()
    lidar.start_motor()
    time.sleep(1)

def backgroundTest():
    lidar = RPLidar(None, '/dev/ttyUSB0', baudrate=115200, timeout=3)

    try:
        lidar.start_motor()
        time.sleep(1)

        for scan in lidar.iter_scans():
            try:
                front_blocked = False
                back_blocked = False

                for (_, angle, distance) in scan:
                    if (((angle > FRONT_MIN_ANGLE) or (angle < FRONT_MAX_ANGLE)) and
                            (distance < DETECTION_DISTANCE_MM)):
                        front_blocked = True

                    if ((BACK_MIN_ANGLE < angle < BACK_MAX_ANGLE) and
                            (distance < DETECTION_DISTANCE_MM)):
                        back_blocked = True

                should_stop = False
                stop_reason = None

                with state_lock:
                    detection["forwardThing"] = front_blocked
                    detection["backwardThing"] = back_blocked

                    commanded_y = motion_state["y"]

                    if commanded_y > 0 and front_blocked:
                        should_stop = True
                        stop_reason = "front"
                        motion_state["y"] = 0.0
                        motion_state["stopped_by_lidar"] = True
                    elif commanded_y < 0 and back_blocked:
                        should_stop = True
                        stop_reason = "back"
                        motion_state["y"] = 0.0
                        motion_state["stopped_by_lidar"] = True
                    else:
                        motion_state["stopped_by_lidar"] = False

                if should_stop:
                    stop_drive()

            except Exception as e:
                print("Scan processing error:", repr(e))

    except Exception as e:
        print("LIDAR failure:", repr(e))
        restart_lidar(lidar)

    finally:
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()


def remove_punctuation_translate(text):
    # Create a translation table that maps every punctuation character to None (deletion)
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)



def tts(text, pitch):
    os.system(f"espeak-ng -v EN-gb-scotland -a 20 -p {pitch} -s 50 '{text}'")

#servo = Controller()
@app.route("/")
def index():
    #allows for set seeding
    if(len(sys.argv)>1):
        random.seed(sys.argv[1])
    print("Flask server was initially connected to or reloaded")
    global d
    global c
    global state
    global variables
    variables = {"name": "i don't know", "age": "i don't know", "color": "i don't know"}
    state = 'boot'
    #ensures that if the webpage is reloaded, all servos are reset
    motor.fullReset()
    with state_lock:
        motion_state["y"] = 0.0
        motion_state["x"] = 0.0
        motion_state["stopped_by_lidar"] = False
    return render_template("index.html")

@app.route("/joystick", methods=["POST"])
def joystick():
    #data is sent
    data = request.json
    x = float(data.get("x", 0))
    y = float(data.get("y", 0))
    #handles bad joystick inputs (data is validated)
    if(math.fabs(x) > 1 or math.fabs(y) > 1):
        return jsonify({"status": "bad"})

    with state_lock:
        front_blocked = detection["forwardThing"]
        back_blocked = detection["backwardThing"]

    print(f"Joystick X: {x}, Y: {y}")
    print("Forward object", front_blocked)
    print("Backward object", back_blocked)

    yAxis = int(1200 * y)
    xAxis = int(1000 * x)

    # Prevent forward movement if something is too close in front
    if y > 0 and front_blocked:
        yAxis = 0
        y = 0.0
        print("Blocked: obstacle in front")

    # Prevent backward movement if something is too close in back
    if y < 0 and back_blocked:
        yAxis = 0
        y = 0.0
        print("Blocked: obstacle in back")

    with state_lock:
        motion_state["y"] = y
        motion_state["x"] = x
        motion_state["stopped_by_lidar"] = False

    #data is interpreted and translated into servo control
    motor.leftWheel(STOP_PWM - yAxis - xAxis)
    motor.rightWheel(STOP_PWM + yAxis - xAxis)
    return jsonify({"status": "ok", "front_blocked": front_blocked, "back_blocked": back_blocked})

@app.route("/head", methods=["POST"])
def head_control():
    data = request.json
    tilt = data.get("tilt")
    pan = data.get("pan")
    print(f"Head Tilt: {tilt}, Pan: {pan}")
    panAmount = int(6000 + (1500 * float(pan)))
    tiltAmount = int(6000 + (1500 * float(tilt)))
    motor.headPan(panAmount)
    motor.headTilt(tiltAmount)
    return {"status": "ok"}


@app.route("/buttons", methods=["POST"])
def buttons():
    data = request.json
    button = data.get("button")
    pressed = data.get("pressed")
    if(pressed == True):
        if(button == '1'):
            tts("Hello good chap", "85")
        if(button == '2'):
            tts("Goodbye old pal", "85")
        if(button == '3'):
            tts("RAGHHHHHHH", "5")
        if(button == '4'):
            tts("I am Lying", "60")
    return {"status": "ok"}

@app.route("/text", methods=["POST"])
def text_input():
    global state
    global d
    global c
    global depth
    global scope
    global variables
    if state == 'boot':
        d, c = dialogueParser.parseText('test.txt')
        state = 'idle'
        depth = 0
        scope = []
    data = request.json
    text = data.get("text", "")
    print(f"User text: {text}")
    #cleans up text by turning it to lowercase and removes punctuation
    text = text.strip().lower()
    text = remove_punctuation_translate(text)
    returnedText, returnedAction, depth, scope, variables = dialogueParser.interpretText(text, d,c ,depth, scope, variables)
    print("returned text:" , returnedText)
    print("action:", returnedAction)
    print("state:", state)
    tts(returnedText, 10)
    if(depth >= 5):
        tts("Error: too deep. Resetting.")
        scope = []
    else:
        if(returnedText == "OK. Stopping now."):
            state = 'idle'
            scope = []
            motor.fullReset()
        if(returnedAction == 'None'):
            print("No action")
        elif(returnedAction == 'head_yes'):
            action_functions.head_yes()
        elif (returnedAction == 'head_no'):
            action_functions.head_no()
        elif (returnedAction == 'arm_raise'):
            action_functions.arm_raise()
        elif(returnedAction == 'dance90'):
            action_functions.dance90()
        else:
            print("Error: unknown action", returnedAction)
    return jsonify({"response": text})

#Resets all motors when the flask server is started/restarted
motor.fullReset()
thread = threading.Thread(target=backgroundTest, daemon=True)
thread.start()
app.run(host="0.0.0.0", port=5000, debug=False)
