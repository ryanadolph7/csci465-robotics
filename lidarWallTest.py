import time
import math
from adafruit_rplidar import RPLidar
import motor
import threading




# -----------------------------
# CONFIG
# -----------------------------
PORT_NAME = '/dev/ttyUSB0'

TARGET_DISTANCE = 750      # mm (distance from wall)
TOLERANCE = 25           # buffer zone

FRONT_THRESHOLD = 500     # obstacle distance
LOST_WALL_DISTANCE = 1200 # if wall too far → considered lost

BASE_SPEED = 600          # forward speed
TURN_ADJUST = 300         # steering strength

# -----------------------------
# SHARED SENSOR DATA
# -----------------------------
sensor_data = {
    "front": 9999,
    "right": 9999
}

# -----------------------------
# LIDAR THREAD
# -----------------------------

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



# -----------------------------
# MOTOR HELPERS
# -----------------------------
def drive(forward, turn):
    left = 6000 - forward - turn
    right = 6000 + forward - turn
    print(left, " ", right)
    motor.leftWheel(left)
    motor.rightWheel(right)

def stop():
    motor.leftWheel(6000)
    motor.rightWheel(6000)

# -----------------------------
# MAIN CONTROL LOOP
# -----------------------------
def main():
    motor.fullReset()
    #time.sleep(7)

    while True:
        front = sensor_data["front"]
        rightData = sensor_data["right"]
        #if(front or right == 9999):
            #print("lidar not working")
        #else:
        # If LIDAR is reading jumble/default values, do nothing
        if front == 9999.0 and rightData == 9999.0:
            print("LIDAR not ready / bad reading → doing nothing")
            stop()
            time.sleep(0.1)
            continue
        left = 6000
        right = 6000
        print(f"Front: {front:.1f} | Right: {rightData:.1f}")

        # -------------------------
        # CASE 1: obstacle in front
        # -------------------------
        if front < FRONT_THRESHOLD:
            print("Obstacle ahead → turning left")
            right = 6850
            left = 6000
            #drive(0, -TURN_ADJUST)  # turn left
            

        # -------------------------
        # CASE 4: wall lost
        # -------------------------
        elif rightData > LOST_WALL_DISTANCE:
            print("Wall lost → searching right")
            left = 5250
            right = 6650
            #drive(BASE_SPEED // 2, TURN_ADJUST)  # turn right
            

        # -------------------------
        # CASE 2: too close to wall
        # -------------------------
        elif rightData < TARGET_DISTANCE - TOLERANCE:
            print("Too close → steering left")
            right = 6950
            left = 5400
            #drive(BASE_SPEED, -TURN_ADJUST)

        # -------------------------
        # CASE 3: too far from wall
        # -------------------------
        elif rightData > TARGET_DISTANCE + TOLERANCE:
            print("Too far → steering right")
            left = 5200
            right = 6650
            #drive(BASE_SPEED, TURN_ADJUST)

        # -------------------------
        # GOOD POSITION
        # -------------------------
        else:
            print("On track → straight")
            left = 5300
            right = 6750
            #drive(BASE_SPEED, 0)
        print("Left wheel:", left, "right wheel:", right)
        motor.leftWheel(left)
        motor.rightWheel(right)
        time.sleep(0.01)

# -----------------------------
# STARTUP
# -----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=lidar_thread, daemon=True)
    t.start()
    time.sleep(4)

    main()