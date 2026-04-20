import time
import math
from adafruit_rplidar import RPLidar
import motor
import threading

# -----------------------------
# CONFIG
# -----------------------------
PORT_NAME = '/dev/ttyUSB0'

TARGET_DISTANCE = 500      # mm (distance from wall)
TOLERANCE = 100           # buffer zone

FRONT_THRESHOLD = 400     # obstacle distance
LOST_WALL_DISTANCE = 1200 # if wall too far → considered lost

BASE_SPEED = 800          # forward speed
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
def lidar_thread():
    lidar = RPLidar(None, PORT_NAME, timeout=3)

    while True:
        for scan in lidar.iter_scans():
            front_vals = []
            right_vals = []

            for (_, angle, distance) in scan:

                # FRONT: 340–20
                if angle > 340 or angle < 20:
                    front_vals.append(distance)

                # RIGHT: 250–290
                if 250 < angle < 290:
                    right_vals.append(distance)

            # Use minimum distance (more reactive)
            if front_vals:
                sensor_data["front"] = min(front_vals)

            if right_vals:
                sensor_data["right"] = min(right_vals)

# -----------------------------
# MOTOR HELPERS
# -----------------------------
def drive(forward, turn):
    left = 6000 - forward - turn
    right = 6000 + forward - turn
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

    while True:
        front = sensor_data["front"]
        right = sensor_data["right"]

        print(f"Front: {front:.1f} | Right: {right:.1f}")

        # -------------------------
        # CASE 1: obstacle in front
        # -------------------------
        if front < FRONT_THRESHOLD:
            print("Obstacle ahead → turning left")
            drive(0, TURN_ADJUST)  # turn left
            time.sleep(0.1)
            continue

        # -------------------------
        # CASE 4: wall lost
        # -------------------------
        if right > LOST_WALL_DISTANCE:
            print("Wall lost → searching right")
            drive(BASE_SPEED // 2, -TURN_ADJUST)  # turn right
            time.sleep(0.1)
            continue

        # -------------------------
        # CASE 2: too close to wall
        # -------------------------
        if right < TARGET_DISTANCE - TOLERANCE:
            print("Too close → steering left")
            drive(BASE_SPEED, TURN_ADJUST)

        # -------------------------
        # CASE 3: too far from wall
        # -------------------------
        elif right > TARGET_DISTANCE + TOLERANCE:
            print("Too far → steering right")
            drive(BASE_SPEED, -TURN_ADJUST)

        # -------------------------
        # GOOD POSITION
        # -------------------------
        else:
            print("On track → straight")
            drive(BASE_SPEED, 0)

        time.sleep(0.05)

# -----------------------------
# STARTUP
# -----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=lidar_thread, daemon=True)
    t.start()

    main()