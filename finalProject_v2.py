import os
import time

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import wave
import json

from scipy.signal import resample
from vosk import Model, KaldiRecognizer
import motor
import lidarWallTest_smooth_fixed
from adafruit_rplidar import RPLidar
import threading


sensor_data = {
    "front": 9999,
    "right": 9999,
    "left": 9999
}

FRONT_THRESHOLD = 400
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
            left_vals = []

            for (_, angle, distance) in scan:

                # FRONT: 340–20
                if angle > 340 or angle < 20:
                    front_vals.append(distance)

                # RIGHT: 40-80
                if 30 < angle < 90:
                    right_vals.append(distance)

                if 270 < angle < 330:
                    left_vals.append(distance)

            # Use minimum distance (more reactive)
            if front_vals:
                sensor_data["front"] = min(front_vals)

            if right_vals:
                sensor_data["right"] = np.median(right_vals)

            if left_vals:
                sensor_data["left"] = np.median(left_vals)

    except Exception as e:
        print("LIDAR failure:", repr(e))
        restart_lidar(lidar)

    finally:
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()

def tts(text):
    os.system(f"espeak-ng -v EN-gb-scotland -a 30 -p {30} -s 50 '{text}'")

def goUntilT():
    MISSING_WALL = 1800
    print(sensor_data["left"], sensor_data["right"])
    while(sensor_data["left"] < MISSING_WALL or sensor_data["right"] < MISSING_WALL):
        motor.leftWheel(5500)
        motor.rightWheel(6500)
    motor.leftWheel(6000)
    motor.rightWheel(6000)
    return True

def alignToHall():
    FRONT_THRESHOLD = 500
    LOST_WALL_DISTANCE = 1800

    STOP_VALUE = 6000
    BASE_SPEED = 750

    RIGHT_MOTOR_TRIM = 50

    LEFT_MIN = 5100
    LEFT_MAX = 5900

    RIGHT_MIN = 6100
    RIGHT_MAX = 7100

    TOLERANCE = 160

    # Lower KP = less aggressive steering
    # Higher KD = slows down fast left/right changes
    KP = 0.10
    KD = 0.12

    MAX_STEER = 180

    STEER_ALPHA = 0.08
    MOTOR_RAMP = 20
    LOOP_DELAY = 0.04

    motor.fullReset()

    smoothed_steer = 0.0
    previous_error = 0.0

    current_left = float(STOP_VALUE - BASE_SPEED)
    current_right = float(STOP_VALUE + BASE_SPEED + RIGHT_MOTOR_TRIM)

    while True:
        front = sensor_data["front"]
        left = sensor_data["left"]
        right = sensor_data["right"]

        print(f"Front: {front:.1f} | Left: {left:.1f} | Right: {right:.1f}")

        if front == 9999 and left == 9999 and right == 9999:
            print("Bad LIDAR reading -> stopping")
            stop()
            time.sleep(0.1)
            continue

        if front < FRONT_THRESHOLD:
            print("Obstacle ahead -> stopping")
            stop()
            time.sleep(0.1)
            continue

        if left > LOST_WALL_DISTANCE and right > LOST_WALL_DISTANCE:
            print("Both walls lost -> hallway/opening detected")
            stop()
            return True

        if left < LOST_WALL_DISTANCE and right < LOST_WALL_DISTANCE:
            center_error = left - right

            if abs(center_error) <= TOLERANCE:
                center_error = 0
                desired_steer = 0
                print("Centered -> straight")
            else:
                derivative = center_error - previous_error
                desired_steer = KP * center_error + KD * derivative

                if center_error > 0:
                    print("Too close to right wall -> steering left gently")
                else:
                    print("Too close to left wall -> steering right gently")

            previous_error = center_error

        elif left < LOST_WALL_DISTANCE and right >= LOST_WALL_DISTANCE:
            print("Only left wall visible -> gently steering right")
            desired_steer = -120
            previous_error = 0

        elif right < LOST_WALL_DISTANCE and left >= LOST_WALL_DISTANCE:
            print("Only right wall visible -> gently steering left")
            desired_steer = 120
            previous_error = 0

        else:
            desired_steer = 0
            previous_error = 0

        desired_steer = clamp(desired_steer, -MAX_STEER, MAX_STEER)

        smoothed_steer = (
            (1 - STEER_ALPHA) * smoothed_steer
            + STEER_ALPHA * desired_steer
        )

        # Important:
        # Left motor is inverse of right motor.
        #
        # Positive steer = turn left:
        #   left command moves closer to 6000, slowing left forward motion
        #   right command moves farther above 6000, speeding right forward motion
        #
        # Negative steer = turn right:
        #   left command moves farther below 6000, speeding left forward motion
        #   right command moves closer to 6000, slowing right forward motion

        target_left = STOP_VALUE - BASE_SPEED + smoothed_steer
        target_right = STOP_VALUE + BASE_SPEED + smoothed_steer + RIGHT_MOTOR_TRIM

        target_left = clamp(target_left, LEFT_MIN, LEFT_MAX)
        target_right = clamp(target_right, RIGHT_MIN, RIGHT_MAX)

        current_left = ramp_toward(current_left, target_left, MOTOR_RAMP)
        current_right = ramp_toward(current_right, target_right, MOTOR_RAMP)

        print(
            f"Center error: {left - right:.1f} | "
            f"Desired steer: {desired_steer:.1f} | "
            f"Smoothed steer: {smoothed_steer:.1f} | "
            f"Left: {current_left:.0f} | "
            f"Right: {current_right:.0f}"
        )

        motor.leftWheel(int(current_left))
        motor.rightWheel(int(current_right))

        time.sleep(LOOP_DELAY)

def clamp(value, low, high):
    return max(low, min(high, value))


def ramp_toward(current, target, max_step):
    if target > current + max_step:
        return current + max_step
    if target < current - max_step:
        return current - max_step
    return target


def stop():
    motor.leftWheel(6000)
    motor.rightWheel(6000)

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

            # Keep listening until the robot understands a valid destination.
            # Valid keywords are: "bathroom" or "lab".
            fs = 48000          # your mic's native rate
            target_fs = 16000   # Vosk-required rate
            seconds = 3

            model = Model("model")
            LOCATION = None

            while LOCATION is None:
                # -------------------
                # RECORD AUDIO
                # -------------------
                print("Recording...")
                audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                print("Done!")

                # Convert to 1D array
                audio = audio.flatten()

                # -------------------
                # RESAMPLE TO 16kHz
                # -------------------
                num_samples = int(len(audio) * target_fs / fs)
                audio_resampled = resample(audio, num_samples).astype(np.int16)

                # Save resampled audio
                write("test.wav", target_fs, audio_resampled)

                # -------------------
                # LOAD AUDIO FOR VOSK
                # -------------------
                wf = wave.open("test.wav", "rb")
                rec = KaldiRecognizer(model, wf.getframerate())

                # -------------------
                # PROCESS AUDIO
                # -------------------
                recognized_text = ""

                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break

                    # Debug: show partial recognition
                    partial = json.loads(rec.PartialResult())
                    if partial.get("partial"):
                        print("partial:", partial["partial"])

                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "")
                        if text:
                            recognized_text += " " + text

                # Always grab final result
                final_result = json.loads(rec.FinalResult())
                final_text = final_result.get("text", "")
                if final_text:
                    recognized_text += " " + final_text

                wf.close()

                recognized_text = recognized_text.lower().strip()
                print("Heard:", recognized_text)

                # -------------------
                # COMMAND LOGIC
                # -------------------
                if "bathroom" in recognized_text:
                    LOCATION = "Bathroom"
                elif "lab" in recognized_text:
                    LOCATION = "Lab"
                else:
                    print("Did not understand a valid destination. Listening again...")
                    tts("Sorry, I did not understand. Please say bathroom or lab.")
                    time.sleep(0.5)

            print("LOCATION:", LOCATION)
            STATE = "TURNING_AROUND"
        elif(STATE == "TURNING_AROUND"):
            tts("Follow Me!")
            #robot 180's
            motor.rightWheel(7500)
            motor.leftWheel(7500)
            time.sleep(1.1)
            motor.rightWheel(6000)
            motor.leftWheel(6000)
            STATE = "ALIGNING_TO_HALLWAY"
        elif(STATE == "ALIGNING_TO_HALLWAY"):
            alignToHall()
            #robot centers itself
            STATE = "MOVING_TO_T"
        elif(STATE == "MOVING_TO_T"):
            #need to detect if hallway dissapears on both sides
            STATE = "TURNING_TO_DESTINATION"
            #otherwise keep moving forward
        elif(STATE == "TURNING_TO_DESTINATION"):
            # Turn left or right
            if(LOCATION == "Bathroom"):
                #turn left
                motor.rightWheel(7200)
                time.sleep(0.5)
                motor.rightWheel(6000)
            elif(LOCATION == "Lab"):
                # turn right 
                motor.leftWheel(5000)
                time.sleep(0.5)
                motor.leftWheel(6000)
            #else:
                #turn left
                #motor.rightWheel(7500)
                #time.sleep(.5)
                #motor.rightWheel(6000)
            STATE = "FINAL_MOVEMENT"
        elif(STATE == "FINAL_MOVEMENT"):
            #move forward for 5 second
            STATE = "STOPPED"
            motor.rightWheel(6700)
            motor.leftWheel(5300)
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