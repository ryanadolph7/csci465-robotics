import keyboard
from maestro import Controller
import time
import os

servo = Controller()

def on_key_down(event):
	neut = 6000
	forward_l = 4800
	forward_r = 7200
	left_l = 7000
	left_r = 7000
	right_l = 5000
	right_r = 5000
	back_l = 7200
	back_r = 4800
 
	if event.name == 'w': # move forward
		servo.setAccel(1, 4)
		servo.setAccel(2, 4)
		servo.setTarget(1, forward_l)
		servo.setTarget(2, forward_r)
	elif event.name == 'a': # move left
		servo.setAccel(1, 4)
		servo.setAccel(2, 4)
		servo.setTarget(1, left_l)
		servo.setTarget(2, left_r)
	elif event.name == 'd':  # move right
		servo.setAccel(1, 4)
		servo.setAccel(2, 4)
		servo.setTarget(1, right_l)
		servo.setTarget(2, right_r)
	elif event.name == 's': # move backwards
		servo.setAccel(1, 4)
		servo.setAccel(2, 4)
		servo.setTarget(1, back_l)
		servo.setTarget(2, back_r)
	elif event.name == 'q':	# reset all servos
		for i in range(18):
			servo.setAccel(i, 4)
			servo.setTarget(i, 6000)
	elif event.name == 'left': # pan head left
		servo.setAccel(3,4)
		servo.setTarget(3, 4500)
	elif event.name == 'right': # pan head right
		servo.setAccel(3, 4)
		servo.setTarget(3, 7500)
	elif event.name == 'up': # tilt head down
		servo.setAccel(4, 4)
		servo.setTarget(4, 7500)
	elif event.name == 'down': # tilt head down
		servo.setAccel(4, 4)
		servo.setTarget(4, 4500)
	elif event.name == '1': # move waist left
		servo.setAccel(6, 4)
		servo.setTarget(6, 4500)
	elif event.name == '2':	# move waist right
		servo.setAccel(6, 4)
		servo.setTarget(6, 7500) 

def on_key_event(event):
	neut = 6000
	if event.event_type == keyboard.KEY_DOWN:
		os.system('clear')
		print(f"Key pressed: {event.name}")
		on_key_down(event)

# Hook all keyboard events
keyboard.hook(on_key_event)

print("Listening for key presses... Press ESC to quit.")

# Wait until ESC is pressed
keyboard.wait('esc')

print("Program ended.")
