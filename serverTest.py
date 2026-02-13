import time

from flask import Flask, render_template, request, jsonify
from maestro import Controller
app = Flask(__name__)

servo = Controller()
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/joystick", methods=["POST"])
def joystick():
    data = request.json
    time.sleep(2)
    x = data.get("x")
    y = data.get("y")

    print(f"Joystick X: {x}, Y: {y}")
    yAxis = int(1200*float(y))
    xAxis = int(1000 * float(x))
    servo.setAccel(1, 5)
    servo.setAccel(2,5)
    servo.setTarget(1, 6000-yAxis-xAxis)
    servo.setTarget(2, 6000+yAxis-xAxis)
    return jsonify({"status": "ok"})

@app.route("/head", methods=["POST"])
def head_control():
    data = request.json
    tilt = data.get("tilt")
    pan = data.get("pan")
    
    print(f"Head Tilt: {tilt}, Pan: {pan}")
    panAmount = int(6000 + (1500 * float(pan)))
    tiltAmount = int(6000 + (1500 * float(tilt)))
    servo.setAccel(3, 4)
    servo.setTarget(3, panAmount)
    servo.setAccel(4, 4)
    servo.setTarget(4, tiltAmount)

    return {"status": "ok"}


@app.route("/buttons", methods=["POST"])
def buttons():
    data = request.json
    button = data.get("button")
    pressed = data.get("pressed")
    if(pressed == True):
        print(f"Button {button} pressed")
    return {"status": "ok"}

app.run(host="0.0.0.0", port=5000, debug=False)
