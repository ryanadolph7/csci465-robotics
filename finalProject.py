import os
import time
import sounddevice as sd
from scipy.io.wavfile import write
import wave
import json
from vosk import Model, KaldiRecognizer
import motor
from adafruit_rplidar import RPLidar
import threading

sensor_data = {
    "front": 9999,
    "right": 9999
}

FRONT_THRESHOLD = 200
api_key = 'd71a9e57cc704cbdb50e5a7b6679e478'

def restart_lidar(lidar):
    print("Trying to restart lidar")
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

def lidar_thread():
    lidar = RPLidar(None, '/dev/ttyUSB0', timeout=3)
    restart_lidar(lidar)
    time.sleep(7)

    try:
        lidar.start_motor()
        time.sleep(1)
        for scan in lidar.iter_scans():
            front_vals = []
            right_vals = []

            for (_, angle, distance) in scan:

                # FRONT: 340–20
                if angle > 340 or angle < 20:
                    front_vals.append(distance)

                # RIGHT: 40-80
                if 30 < angle < 90:
                    right_vals.append(distance)

            # Use minimum distance (more reactive)
            if front_vals:
                sensor_data["front"] = min(front_vals)

            if right_vals:
                sensor_data["right"] = min(right_vals)

    except Exception as e:
        print("LIDAR failure:", repr(e))
        restart_lidar(lidar)

    finally:
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()

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
        elif (STATE == "GREETING"):
            # robot says "hello nice to meet you"
            tts("Hello, how can I help you?")
            STATE = "LISTENING"
        elif(STATE == "LISTENING"):

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
        elif(STATE == "TURNING_AROUND"):
            #robot 180's
            motor.rightWheel(7000)
            time.sleep(0.5)
            motor.rightWheel(6000)
            STATE = "ALIGNING_TO_HALLWAY"
        elif(STATE == "ALIGNING_TO_HALLWAY"):
            #robot centers itself
            STATE = "MOVING_TO_T"
        elif(STATE == "MOVING_TO_T"):
            #need to detect if hallway dissapears on both sides
            if(True):
                STATE = "TURNING_TO_DESTINATION"
            #otherwise keep moving forward
        elif(STATE == "TURNING_TO_DESTINATION"):
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
        elif(STATE == "FINAL_MOVEMENT"):
            #move forward for 5 second
            STATE = "STOPPED"
            motor.rightWheel(6500)
            motor.leftWheel(5500)
            time.sleep(5)
            motor.rightWheel(6000)
            motor.leftWheel(6000)
        elif(STATE == "STOPPED"):
            #robot says "we're here"
            tts("We're here!")
            STATE = "DONE"

        time.sleep(0.5)


if __name__ == "__main__":
    t = threading.Thread(target=lidar_thread, daemon=True)
    t.start()
    time.sleep(4)

    main()