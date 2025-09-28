import machine
from machine import Pin, I2C
import time
import os
import ds3231  # RTC library

# --- RTC Setup ---
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)
rtc = ds3231.DS3231(i2c)

def format_time(dt):
    _, _, _, _, hour, minute, second, _ = dt
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def format_date(dt):
    year, month, day, _, _, _, _, _ = dt
    return f"{year:04d}-{month:02d}-{day:02d}"

# --- Data folder setup ---
if "Data" not in os.listdir():
    os.mkdir("Data")

# --- Beam Sensors ---
gate1 = Pin(15, Pin.IN, Pin.PULL_UP)  # Left
gate2 = Pin(14, Pin.IN, Pin.PULL_UP)  # Right

DEBOUNCE = 200  # ms
last_trigger_gate1 = 0
last_trigger_gate2 = 0

sequence = []  # Track gate sequence

# --- Test Control Button + LED ---
test_button = Pin(8, Pin.IN, Pin.PULL_UP)  # Toggle button
status_led = Pin(13, Pin.OUT)              # Onboard LED
test_active = False
file_name = None

# --- Logging ---
def log_event(timestamp, direction):
    global file_name, test_active
    if not test_active:
        return
    print(f"{timestamp} - {direction}")
    with open(file_name, 'a') as f:
        f.write(f"{timestamp},{direction}\n")

# --- Gate Callbacks ---
def gate1_trigger(pin):
    global last_trigger_gate1, sequence
    if not test_active:
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, last_trigger_gate1) > DEBOUNCE:
        timestamp = format_time(rtc.datetime())
        sequence.append(("L", timestamp))
        check_direction()
        last_trigger_gate1 = now

def gate2_trigger(pin):
    global last_trigger_gate2, sequence
    if not test_active:
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, last_trigger_gate2) > DEBOUNCE:
        timestamp = format_time(rtc.datetime())
        sequence.append(("R", timestamp))
        check_direction()
        last_trigger_gate2 = now

# --- Direction Check ---
def check_direction():
    global sequence
    if len(sequence) >= 2:
        first_gate, first_time = sequence[0]
        second_gate, second_time = sequence[1]
        if first_gate == "L" and second_gate == "R":
            log_event(second_time, "Right")
        elif first_gate == "R" and second_gate == "L":
            log_event(second_time, "Left")
        sequence = []  # Reset

# --- Test Toggle ---
def toggle_test(pin):
    global test_active, file_name
    time.sleep_ms(50)  # debounce
    if pin.value() == 0:  # button pressed
        test_active = not test_active
        if test_active:
            # Start new test
            dt = rtc.datetime()
            file_name = f"Data/{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}_{dt[4]:02d}-{dt[5]:02d}-{dt[6]:02d}.csv"
            with open(file_name, 'w') as f:
                f.write(f"Date:,{format_date(dt)}\n")
                f.write("Time,Direction\n")
            print("Test started:", file_name)
            status_led.on()
        else:
            # Stop test
            print("Test stopped")
            status_led.off()

# --- Attach interrupts ---
gate1.irq(trigger=Pin.IRQ_FALLING, handler=gate1_trigger)
gate2.irq(trigger=Pin.IRQ_FALLING, handler=gate2_trigger)
test_button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_test)

# --- Main loop ---
while True:
    time.sleep(1)
