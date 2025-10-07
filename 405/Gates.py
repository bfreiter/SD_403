import machine
from machine import Pin, I2C, SPI
import time
import os
import json
import ds3231
import sdcard

# =========================================================
# --- Load Config ---
# =========================================================
CONFIG_FILE = "config.json"

def load_config(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Failed to load config:", e)
        return None

config = load_config(CONFIG_FILE)
if not config:
    raise Exception("Cannot continue without a valid config file")

# =========================================================
# --- RTC Setup ---
# =========================================================
i2c = I2C(0, scl=Pin(config["rtc_i2c"]["scl"]), sda=Pin(config["rtc_i2c"]["sda"]), freq=config["rtc_i2c"]["freq"])
rtc = ds3231.DS3231(i2c)

def format_time(dt):
    _, _, _, _, hour, minute, second, _ = dt
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def format_date(dt):
    year, month, day, _, _, _, _, _ = dt
    return f"{year:04d}-{month:02d}-{day:02d}"

# =========================================================
# --- CSV / Data Setup ---
# =========================================================
DATA_DIR = config["data_dir"]
if DATA_DIR not in os.listdir():
    os.mkdir(DATA_DIR)

file_name = None
test_running = False

# =========================================================
# --- LEDs and Buzzer ---
# =========================================================
status_led = Pin(config["status_led_pin"], Pin.OUT)
sd_led = Pin(config["sd_led_pin"], Pin.OUT)
buzzer = Pin(config["buzzer_pin"], Pin.OUT)

# Reset LEDs and buzzer at startup
status_led.value(0)
sd_led.value(0)
buzzer.value(0)

# Buzzer debounce
last_buzzer_trigger = 0
BUZZER_DEBOUNCE = 200  # ms

def beep(duration_ms=100):
    global last_buzzer_trigger
    now = time.ticks_ms()
    if time.ticks_diff(now, last_buzzer_trigger) < BUZZER_DEBOUNCE:
        return
    last_buzzer_trigger = now
    buzzer.value(1)
    time.sleep_ms(duration_ms)
    buzzer.value(0)

# =========================================================
# --- Beam Sensors ---
# =========================================================
Right_Left  = Pin(config["beam_pins"]["Right_Left"], Pin.IN, Pin.PULL_UP)
Right_Right = Pin(config["beam_pins"]["Right_Right"], Pin.IN, Pin.PULL_UP)
Left_Left   = Pin(config["beam_pins"]["Left_Left"], Pin.IN, Pin.PULL_UP)
Left_Right  = Pin(config["beam_pins"]["Left_Right"], Pin.IN, Pin.PULL_UP)

DEBOUNCE = config["debounce_ms"]
last_trigger = {"Right_Left": 0, "Right_Right": 0, "Left_Left": 0, "Left_Right": 0}
sequence = []

# =========================================================
# --- SD Card Setup ---
# =========================================================
spi = SPI(1, baudrate=config["spi"]["baudrate"], sck=Pin(config["spi"]["sck"]),
          mosi=Pin(config["spi"]["mosi"]), miso=Pin(config["spi"]["miso"]))
cs = Pin(config["spi"]["cs"], Pin.OUT)
det_pin = Pin(config["sd_detect_pin"], Pin.IN)
source = "/Data"
destination = config["sd_destination"]
sd_present = False

# =========================================================
# --- Buttons ---
# =========================================================
test_button = Pin(config["test_button_pin"], Pin.IN, Pin.PULL_UP)
download_button = Pin(config["download_button_pin"], Pin.IN, Pin.PULL_UP)
last_download_trigger = 0
DEBOUNCE_MS = config["download_debounce_ms"]

# =========================================================
# --- Logging ---
# =========================================================
def log_event(timestamp, pair, direction):
    if test_running and file_name:
        print(f"{timestamp} - {pair} - {direction}")
        with open(file_name, 'a') as f:
            f.write(f"{timestamp},{pair},{direction}\n")

# =========================================================
# --- Direction Detection ---
# =========================================================
def check_direction():
    global sequence
    if len(sequence) >= 2:
        first_gate, _ = sequence[0]
        second_gate, second_time = sequence[1]

        if first_gate.startswith("Left") and second_gate.startswith("Left"):
            direction = "Right" if first_gate == "Left_Left" else "Left"
            log_event(second_time, "Left Pair", direction)
        elif first_gate.startswith("Right") and second_gate.startswith("Right"):
            direction = "Right" if first_gate == "Right_Left" else "Left"
            log_event(second_time, "Right Pair", direction)

        sequence = []

# =========================================================
# --- Beam Gate Interrupts ---
# =========================================================
def make_gate_callback(name):
    def callback(pin):
        global last_trigger, sequence
        if not test_running:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, last_trigger[name]) > DEBOUNCE:
            sequence.append((name, format_time(rtc.datetime())))
            check_direction()
            last_trigger[name] = now
    return callback

for name, pin in [("Right_Left", Right_Left), ("Right_Right", Right_Right),
                  ("Left_Left", Left_Left), ("Left_Right", Left_Right)]:
    pin.irq(trigger=Pin.IRQ_FALLING, handler=make_gate_callback(name))

# =========================================================
# --- Test Control ---
# =========================================================
def start_new_test():
    global file_name, test_running
    dt = rtc.datetime()
    file_name = f"{DATA_DIR}/{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}_{dt[4]:02}-{dt[5]:02}-{dt[6]:02}.csv"
    with open(file_name, 'w') as f:
        f.write(f"Date:,{format_date(dt)}\n")
        f.write("Time,Pair,Direction\n")
    test_running = True
    status_led.value(1)
    print(f"Started new test, logging to {file_name}")

def stop_test():
    global test_running
    test_running = False
    status_led.value(0)
    print("Test stopped, logging disabled")

def test_toggle_callback(pin):
    beep()
    if test_button.value() == 0:
        if test_running:
            stop_test()
        else:
            start_new_test()

test_button.irq(trigger=Pin.IRQ_FALLING, handler=test_toggle_callback)

# =========================================================
# --- SD Functions ---
# =========================================================
def mount_sd():
    global sd_present
    try:
        sd = sdcard.SDCard(spi, cs)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        sd_present = True
    except OSError:
        sd_present = False

def folder_exists(path):
    try:
        os.listdir(path)
        return True
    except OSError:
        return False

def copy_files(source, destination):
    try:
        os.mkdir(destination)
    except OSError:
        pass
    for item in os.listdir(source):
        src_path = f"{source}/{item}"
        dest_path = f"{destination}/{item}"
        if os.stat(src_path)[0] & 0x4000:
            copy_files(src_path, dest_path)
        else:
            with open(src_path, 'rb') as fsrc, open(dest_path, 'wb') as fdest:
                while True:
                    buf = fsrc.read(1024)
                    if not buf:
                        break
                    fdest.write(buf)

def delete_files(path):
    for item in os.listdir(path):
        item_path = f"{path}/{item}"
        try:
            if os.stat(item_path)[0] & 0x4000:
                delete_files(item_path)
                os.rmdir(item_path)
            else:
                os.remove(item_path)
        except OSError as e:
            print("Error deleting", item_path, ":", e)

def ensure_sd_data_folder():
    try:
        if 'Data' not in os.listdir('/sd'):
            os.mkdir('/sd/Data')
    except OSError as e:
        print(f"Failed to create /sd/Data: {e}")

# =========================================================
# --- SD Download Callback ---
# =========================================================
def download_callback(pin):
    beep()
    global sd_present, last_download_trigger
    now = time.ticks_ms()
    if time.ticks_diff(now, last_download_trigger) < DEBOUNCE_MS:
        return
    last_download_trigger = now

    if det_pin.value() == 1:
        mount_sd()
        if not sd_present:
            print("SD card not detected or failed to mount.")
            return

        ensure_sd_data_folder()

        if not folder_exists(source):
            print(f"Source folder '{source}' not found. Nothing to copy.")
            return

        try:
            if len(os.listdir(source)) > 0:
                copy_files(source, destination)
                print("Data copied to SD card")
                sd_led.value(1)
                delete_files(source)
                print("Local Data folder cleared.")
            else:
                print("No files to copy.")
        except OSError as e:
            print("Error during SD transfer:", e)

        try:
            os.umount("/sd")
        except OSError:
            pass
        sd_present = False

download_button.irq(trigger=Pin.IRQ_FALLING, handler=download_callback)

# =========================================================
# --- SD Detect Callback ---
# =========================================================
def sd_detect_callback(pin):
    global sd_present
    if pin.value() == 1:
        sd_present = True
    else:
        sd_present = False
        sd_led.value(0)

det_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=sd_detect_callback)

# =========================================================
# --- Main Loop ---
# =========================================================
while True:
    time.sleep(1)