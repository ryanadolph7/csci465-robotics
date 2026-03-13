import random
import string
import sys

from flask import Flask, render_template, request, jsonify
from maestro import Controller
app = Flask(__name__)
import os
import math
import dialogueParser
import action_functions
import motor

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
    return render_template("index.html")

@app.route("/joystick", methods=["POST"])
def joystick():
    #data is sent
    data = request.json
    x = data.get("x")
    y = data.get("y")
    #handles bad joystick inputs (data is validated)
    if(math.fabs(x) > 1 or math.fabs(y) > 1):
        return jsonify({"status": "bad"})
    print(f"Joystick X: {x}, Y: {y}")
    yAxis = int(1200*float(y))
    xAxis = int(1000 * float(x))
    #data is interpreted and translated into servo control
    motor.leftWheel(6000-yAxis-xAxis)
    motor.rightWheel(6000+yAxis-xAxis)
    return jsonify({"status": "ok"})

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
app.run(host="0.0.0.0", port=5000, debug=False)
