from machine import Pin, PWM
import time
import ujson

# -------------------------------
# Load configuration from JSON
# -------------------------------
CONFIG_FILE = "config.json"
default_delay = 5

try:
    with open(CONFIG_FILE, "r") as f:
        config = ujson.load(f)
        delay_time = config.get("delay_time", default_delay)
except:
    delay_time = default_delay

# -------------------------------
# Servo setup
# -------------------------------
servo1 = PWM(Pin(18))
servo2 = PWM(Pin(19))
servo1.freq(50)
servo2.freq(50)

def set_servo_angle(servo, angle):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

# -------------------------------
# Servo states
# -------------------------------
servo1_pos = 0
servo2_pos = 0
delayed_flag = False

# -------------------------------
# Buttons (wired to GND)
# -------------------------------
button_servo1 = Pin(2, Pin.IN, Pin.PULL_UP)
button_servo2 = Pin(3, Pin.IN, Pin.PULL_UP)
button_instant = Pin(4, Pin.IN, Pin.PULL_UP)
button_delayed = Pin(5, Pin.IN, Pin.PULL_UP)

# -------------------------------
# Debounce helpers
# -------------------------------
DEBOUNCE_MS = 200
last_press_servo1 = 0
last_press_servo2 = 0
last_press_instant = 0
last_press_delayed = 0

def button_pressed(button, last_time):
    now = time.ticks_ms()
    if not button.value() and time.ticks_diff(now, last_time) > DEBOUNCE_MS:
        return True, now
    return False, last_time

# -------------------------------
# Main loop
# -------------------------------
while True:
    # Servo 1 toggle
    pressed, last_press_servo1 = button_pressed(button_servo1, last_press_servo1)
    if pressed:
        servo1_pos = 90 if servo1_pos == 0 else 0

    # Servo 2 toggle
    pressed, last_press_servo2 = button_pressed(button_servo2, last_press_servo2)
    if pressed:
        servo2_pos = 90 if servo2_pos == 0 else 0

    # Instant toggle both
    pressed, last_press_instant = button_pressed(button_instant, last_press_instant)
    if pressed:
        servo1_pos = 90 if servo1_pos == 0 else 0
        servo2_pos = 90 if servo2_pos == 0 else 0

    # Delayed toggle both
    pressed, last_press_delayed = button_pressed(button_delayed, last_press_delayed)
    if pressed:
        delayed_flag = True

    if delayed_flag:
        time.sleep(delay_time)
        servo1_pos = 90 if servo1_pos == 0 else 0
        servo2_pos = 90 if servo2_pos == 0 else 0
        delayed_flag = False

    # Apply servo positions
    set_servo_angle(servo1, servo1_pos)
    set_servo_angle(servo2, servo2_pos)

    time.sleep(0.01)
