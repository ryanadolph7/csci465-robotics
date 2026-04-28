import os
import time

import motor

sensor_data = {
    "front": 9999,
    "right": 9999
}

FRONT_THRESHOLD = 200


def tts(text, pitch):
    os.system(f"espeak-ng -v EN-gb-scotland -a 30 -p {pitch} -s 50 '{text}'")

def main():
    STATE = "WAITING"
    LOCATION = None
    while True:
        front = sensor_data["front"]
        # wait until human is detected using lidar
        if(STATE == "WAITING"):
            if(front < FRONT_THRESHOLD):
                STATE = "GREETING"
        if (STATE == "GREETING"):
            # robot says "hello nice to meet you"
            tts("Hello, how can I help you?")
            STATE = "LISTENING"
        if(STATE == "LISTENING"):
            #figure out how to do speech recognition
            LOCATION = "Example"
            #robot says "follow me"
            STATE = "TURNING_AROUND"
        if(STATE == "TURNING_AROUND"):
            #robot 180's
            motor.rightWheel(7000)
            time.sleep(0.5)
            motor.rightWheel(6000)
            STATE = "ALIGNING_TO_HALLWAY"
        if(STATE == "ALIGNING_TO_HALLWAY"):
            #robot centers itself
            STATE = "MOVING_TO_T"
        if(STATE == "MOVING_TO_T"):
            #need to detect if hallway dissapears on both sides
            if(True):
                STATE = "TURNING_TO_DESTINATION"
            #otherwise keep moving forward
        if(STATE == "TURNING_TO_DESTINATION"):
            # Turn left or right
            if(LOCATION == "Bathroom"):
                #turn right
                motor.leftWheel(5000)
                time.sleep(0.5)
                motor.leftWheel(6000)
            else:
                #turn left
                motor.rightWheel(7000)
                time.sleep(0.5)
                motor.rightWheel(6000)
            STATE = "FINAL_MOVEMENT"
        if(STATE == "FINAL_MOVEMENT"):
            #move forward for 5 second
            STATE = "STOPPED"
            motor.rightWheel(6500)
            motor.leftWheel(5500)
            time.sleep(5)
            motor.rightWheel(6000)
            motor.leftWheel(6000)
        if(STATE == "STOPPED"):
            #robot says "we're here"
            tts("We're here!")
            STATE = "DONE"

        time.sleep(0.1)