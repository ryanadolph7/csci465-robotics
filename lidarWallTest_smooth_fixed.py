import time
from adafruit_rplidar import RPLidar
import motor
import threading

# -----------------------------
# CONFIG
# -----------------------------
PORT_NAME = '/dev/ttyUSB0'

# Wall-following target
TARGET_DISTANCE = 700       # mm from the right wall
TOLERANCE = 35              # mm deadband around target

# LIDAR thresholds
FRONT_THRESHOLD = 500       # mm; obstacle directly ahead
LOST_WALL_DISTANCE = 1200   # mm; right wall considered lost

# Motor calibration
# These are your known-good straight-driving values.
LEFT_STRAIGHT = 5300
RIGHT_STRAIGHT = 6750
RIGHT_MOTOR_TRIM = 50       # right motor needs about +50 to match left motor

# Smooth steering tuning
KP = 0.55                   # proportional steering gain
MAX_STEER = 450             # maximum normal wall-follow correction
LOST_WALL_STEER = 350       # positive = smoothly search/turn right
OBSTACLE_STEER = -500       # negative = turn left away from obstacle
STEER_ALPHA = 0.15          # lower = smoother/slower, higher = more reactive
MOTOR_RAMP = 35             # maximum motor command change per loop
LOOP_DELAY = 0.03           # seconds

# Motor command safety limits based on your previous working values
LEFT_MIN = 5000
LEFT_MAX = 5700
RIGHT_MIN = 6400
RIGHT_MAX = 7100            # allows RIGHT_MOTOR_TRIM headroom

# -----------------------------
# SHARED SENSOR DATA
# -----------------------------
sensor_data = {
    "front": 9999.0,
    "right": 9999.0
}

# -----------------------------
# LIDAR THREAD
# -----------------------------
def restart_lidar(lidar):
    print("Trying to restart lidar")

    try:
        lidar.stop()
        lidar.stop_motor()
    except Exception:
        pass

    time.sleep(0.5)

    try:
        lidar.disconnect()
    except Exception:
        pass

    time.sleep(0.5)

    lidar.connect()
    lidar.start_motor()
    time.sleep(1)


def lidar_thread():
    lidar = RPLidar(None, PORT_NAME, timeout=3)
    restart_lidar(lidar)
    time.sleep(7)

    try:
        lidar.start_motor()
        time.sleep(1)

        for scan in lidar.iter_scans():
            front_vals = []
            right_vals = []

            for (_, angle, distance) in scan:
                # Ignore invalid zero/negative readings
                if distance <= 0:
                    continue

                # FRONT: 340-360 degrees and 0-20 degrees
                if angle > 340 or angle < 20:
                    front_vals.append(distance)

                # RIGHT side of robot
                if 30 < angle < 90:
                    right_vals.append(distance)

            # Use minimum distance because it is more reactive to nearby obstacles
            if front_vals:
                sensor_data["front"] = min(front_vals)
            else:
                sensor_data["front"] = 9999.0

            if right_vals:
                sensor_data["right"] = min(right_vals)
            else:
                sensor_data["right"] = 9999.0

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

# -----------------------------
# MAIN CONTROL LOOP
# -----------------------------
def lidarIt():
    PORT_NAME = '/dev/ttyUSB0'

    # Wall-following target
    TARGET_DISTANCE = 2000  # mm from the right wall
    TOLERANCE = 35  # mm deadband around target

    # LIDAR thresholds
    FRONT_THRESHOLD = 500  # mm; obstacle directly ahead
    LOST_WALL_DISTANCE = 1200  # mm; right wall considered lost

    # Motor calibration
    # These are your known-good straight-driving values.
    LEFT_STRAIGHT = 5300
    RIGHT_STRAIGHT = 6750
    RIGHT_MOTOR_TRIM = 50  # right motor needs about +50 to match left motor

    # Smooth steering tuning
    KP = 0.55  # proportional steering gain
    MAX_STEER = 450  # maximum normal wall-follow correction
    LOST_WALL_STEER = 350  # positive = smoothly search/turn right
    OBSTACLE_STEER = -500  # negative = turn left away from obstacle
    STEER_ALPHA = 0.15  # lower = smoother/slower, higher = more reactive
    MOTOR_RAMP = 35  # maximum motor command change per loop
    LOOP_DELAY = 0.03  # seconds

    # Motor command safety limits based on your previous working values
    LEFT_MIN = 5000
    LEFT_MAX = 5700
    RIGHT_MIN = 6400
    RIGHT_MAX = 7100  # allows RIGHT_MOTOR_TRIM headroom
    motor.fullReset()

    smoothed_steer = 0.0
    current_left = float(LEFT_STRAIGHT)
    current_right = float(RIGHT_STRAIGHT + RIGHT_MOTOR_TRIM)

    while True:
        front = sensor_data["front"]
        right_data = sensor_data["right"]

        # If LIDAR is reading jumble/default values, stop and wait.
        if front == 9999.0 and right_data == 9999.0:
            print("LIDAR not ready / bad reading -> stopping")
            stop()
            time.sleep(0.1)
            continue

        print(f"Front: {front:.1f} | Right: {right_data:.1f}")

        # -------------------------
        # Decide desired steering
        # -------------------------
        if front < FRONT_THRESHOLD:
            print("Obstacle ahead -> smoothly steering left")
            desired_steer = OBSTACLE_STEER

        elif right_data > LOST_WALL_DISTANCE:
            print("Wall lost -> smoothly searching right")
            desired_steer = LOST_WALL_STEER

        else:
            # Positive error means the robot is too far from the right wall.
            # Negative error means the robot is too close to the right wall.
            error = right_data - TARGET_DISTANCE

            if abs(error) < TOLERANCE:
                error = 0

            # Positive steer turns/searches right.
            # Negative steer moves away from the wall to the left.
            desired_steer = KP * error
            desired_steer = clamp(desired_steer, -MAX_STEER, MAX_STEER)

            if error < 0:
                print("Too close -> smoothly drifting left")
            elif error > 0:
                print("Too far -> smoothly drifting right")
            else:
                print("On track -> straight")
                motor.leftWheel(6000)
                motor.rightWheel(6000)
                return True

        # -------------------------
        # Smooth the steering command
        # -------------------------
        smoothed_steer = ((1 - STEER_ALPHA) * smoothed_steer
                          + STEER_ALPHA * desired_steer)

        # -------------------------
        # Convert steering into motor commands
        # -------------------------
        # With your motor directions:
        #   positive steer = turn right: left wheel faster, right wheel slower
        #   negative steer = turn left:  left wheel slower, right wheel faster
        target_left = LEFT_STRAIGHT - smoothed_steer
        target_right = RIGHT_STRAIGHT - smoothed_steer + RIGHT_MOTOR_TRIM

        target_left = clamp(target_left, LEFT_MIN, LEFT_MAX)
        target_right = clamp(target_right, RIGHT_MIN, RIGHT_MAX)

        # Ramp motor commands so they change slowly instead of jumping.
        current_left = ramp_toward(current_left, target_left, MOTOR_RAMP)
        current_right = ramp_toward(current_right, target_right, MOTOR_RAMP)

        print(
            f"Steer: {smoothed_steer:.1f} | "
            f"Left wheel: {current_left:.0f} | Right wheel: {current_right:.0f}"
        )

        motor.leftWheel(int(current_left))
        motor.rightWheel(int(current_right))

        time.sleep(LOOP_DELAY)

# -----------------------------
# STARTUP
# -----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=lidar_thread, daemon=True)
    t.start()
    time.sleep(4)

    lidarIt()
