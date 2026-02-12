import time

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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

    return jsonify({"status": "ok"})

@app.route("/head", methods=["POST"])
def head_control():
    data = request.json
    tilt = data.get("tilt")
    pan = data.get("pan")

    print(f"Head Tilt: {tilt}, Pan: {pan}")

    return {"status": "ok"}


@app.route("/buttons", methods=["POST"])
def buttons():
    data = request.json
    button = data.get("button")
    pressed = data.get("pressed")
    if(pressed == True):
        print(f"Button {button} pressed")
    return {"status": "ok"}

app.run(host="0.0.0.0", port=8888, debug=False)