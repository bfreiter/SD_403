import machine
from machine import Pin, I2C, SPI
import time
import os
import ds3231
import sdcard

# --- RTC Setup ---
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)
rtc = ds3231.DS3231(i2c)

def format_time(dt):
    _, _, _, _, hour, minute, second, _ = dt
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def format_date(dt):
    year, month, day, _, _, _, _, _ = dt
    return f"{year:04d}-{month:02d}-{day:02d}"

# --- CSV Setup ---
if "Data" not in os.listdir():
    os.mkdir("Data")

file_name = None
test_running = False
test_number = 0

# --- LEDs ---
status_led = Pin(18, Pin.OUT)   # Test running LED
sd_led = Pin(19, Pin.OUT)       # SD card inserted LED

# --- Beam Sensors ---
gate1 = Pin(15, Pin.IN, Pin.PULL_UP)  # Left
gate2 = Pin(14, Pin.IN, Pin.PULL_UP)  # Right

DEBOUNCE = 200  # ms
last_trigger_gate1 = 0
last_trigger_gate2 = 0
sequence = []

# --- SD Card Setup ---
spi = SPI(1, baudrate=1000000,
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))
cs = Pin(13, Pin.OUT)
det_pin = Pin(22, Pin.IN)   # SD detect
source = "/Data"
destination = "/sd/Data"
sd_present = False

# --- Buttons ---
download_button = Pin(9, Pin.IN, Pin.PULL_UP)
last_download_trigger = 0
DEBOUNCE_MS = 300

test_button = Pin(8, Pin.IN, Pin.PULL_UP)

# --- Logging ---
def log_event(timestamp, direction):
    if test_running and file_name:
        print(f"{timestamp} - {direction}")
        with open(file_name, 'a') as f:
            f.write(f"{timestamp},{direction}\n")

# --- Direction Detection ---
def check_direction():
    global sequence
    if len(sequence) >= 2:
        first_gate, first_time = sequence[0]
        second_gate, second_time = sequence[1]

        if first_gate == "L" and second_gate == "R":
            log_event(second_time, "Right")
        elif first_gate == "R" and second_gate == "L":
            log_event(second_time, "Left")

        sequence = []

# --- Beam Gate Interrupts ---
def gate1_trigger(pin):
    global last_trigger_gate1, sequence
    if not test_running:
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, last_trigger_gate1) > DEBOUNCE:
        sequence.append(("L", format_time(rtc.datetime())))
        check_direction()
        last_trigger_gate1 = now

def gate2_trigger(pin):
    global last_trigger_gate2, sequence
    if not test_running:
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, last_trigger_gate2) > DEBOUNCE:
        sequence.append(("R", format_time(rtc.datetime())))
        check_direction()
        last_trigger_gate2 = now

gate1.irq(trigger=Pin.IRQ_FALLING, handler=gate1_trigger)
gate2.irq(trigger=Pin.IRQ_FALLING, handler=gate2_trigger)

# --- Test Start/Stop ---
def start_new_test():
    global file_name, test_number, test_running
    start_time = rtc.datetime()
    test_number += 1
    file_name = f"Data/Test{test_number}_{start_time[0]:04d}-{start_time[1]:02d}-{start_time[2]:02d}_{start_time[4]:02}-{start_time[5]:02}-{start_time[6]:02}.csv"
    with open(file_name, 'w') as f:
        f.write(f"Date:,{format_date(start_time)}\n")
        f.write("Time,Direction\n")
    test_running = True
    status_led.value(1)
    print(f"Started new test #{test_number}, logging to {file_name}")

def stop_test():
    global test_running
    test_running = False
    status_led.value(0)
    print("Test stopped, logging disabled")

def test_toggle_callback(pin):
    time.sleep_ms(50)  # debounce
    if test_button.value() == 0:
        if test_running:
            stop_test()
        else:
            start_new_test()

test_button.irq(trigger=Pin.IRQ_FALLING, handler=test_toggle_callback)

# --- SD Functions ---
def mount_sd():
    global sd_present
    try:
        sd = sdcard.SDCard(spi, cs)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        sd_present = True
    except OSError:
        sd_present = False

def copy_files(source, destination):
    try:
        os.mkdir(destination)
    except OSError:
        pass
    for item in os.listdir(source):
        source_path = f"{source}/{item}"
        destination_path = f"{destination}/{item}"
        if os.stat(source_path)[0] & 0x4000:
            copy_files(source_path, destination_path)
        else:
            with open(source_path, 'rb') as fsource, open(destination_path, 'wb') as fdest:
                while True:
                    buf = fsource.read(1024)
                    if not buf:
                        break
                    fdest.write(buf)

def download_callback(pin):
    global sd_present, last_download_trigger
    now = time.ticks_ms()
    if time.ticks_diff(now, last_download_trigger) < DEBOUNCE_MS:
        return
    last_download_trigger = now

    if det_pin.value() == 1:
        if not sd_present:
            mount_sd()
        try:
            if os.stat(source)[0] & 0x4000:
                copy_files(source, destination)
                print("Data copied to SD card")
        except OSError:
            print("No Data folder found")
        try:
            os.umount("/sd")
        except OSError:
            pass
        sd_present = False

download_button.irq(trigger=Pin.IRQ_FALLING, handler=download_callback)

# --- SD LED via Interrupt ---
def sd_detect_callback(pin):
    global sd_present
    if pin.value() == 1:  # SD inserted
        sd_led.value(1)
    else:                 # SD removed
        sd_led.value(0)
        sd_present = False

det_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=sd_detect_callback)

# --- Main Loop ---
while True:
    time.sleep(1)  # All actions handled via interrupts
