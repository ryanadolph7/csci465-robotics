import os
import time
import sounddevice as sd
from scipy.io.wavfile import write
import wave
import json
from vosk import Model, KaldiRecognizer
import motor

sensor_data = {
    "front": 9999,
    "right": 9999
}

FRONT_THRESHOLD = 200
api_key = 'd71a9e57cc704cbdb50e5a7b6679e478'

def tts(text):
    os.system(f"espeak-ng -v EN-gb-scotland -a 30 -p {30} -s 50 '{text}'")

def main():
    STATE = "WAITING"
    LOCATION = None
    while True:
        print("STATE:", STATE)
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

            fs = 16000  # Vosk works best at 16kHz
            seconds = 5
            model = Model("model")
            LOCATION = "example"
            if (LOCATION == "example"):
                print("Recording...")
                audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                print("Done!")

                write("test.wav", fs, audio)

                wf = wave.open("test.wav", "rb")

                rec = KaldiRecognizer(model, wf.getframerate())

                # -------------------
                # PROCESS AUDIO
                # -------------------
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break

                    if rec.AcceptWaveform(data):
                        if("bathroom" in rec.Result()["text"]):
                            LOCATION = "bathroom"
                        elif("lab" in rec.Result()["text"]):
                            LOCATION = "lab"
                        else:
                            LOCATION = "example"
            #figure out how to do speech recognition
            #robot says "follow me"
            tts("Follow Me!")
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

        time.sleep(0.5)