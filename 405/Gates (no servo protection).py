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

file_name_A = None
file_name_B = None
test_running_A = False
test_running_B = False

# =========================================================
# --- LEDs ---
# =========================================================
status_led_A = Pin(config["status_led_A_pin"], Pin.OUT)
status_led_B = Pin(config["status_led_B_pin"], Pin.OUT)
sd_led = Pin(config["sd_led_pin"], Pin.OUT)

module_led_A = Pin(config["module_led_A_pin"], Pin.OUT)
module_led_B = Pin(config["module_led_B_pin"], Pin.OUT)

status_led_A.value(0)
status_led_B.value(0)
sd_led.value(0)
module_led_A.value(0)
module_led_B.value(0)

# =========================================================
# --- Beam Sensors ---
# =========================================================
DEBOUNCE = config["debounce_ms"]

beam_A_pins = {name: Pin(pin, Pin.IN, Pin.PULL_UP) for name, pin in config["beam_pins_A"].items()}
beam_B_pins = {name: Pin(pin, Pin.IN, Pin.PULL_UP) for name, pin in config["beam_pins_B"].items()}

last_trigger_A = {name: 0 for name in beam_A_pins}
sequence_A = []

last_trigger_B = {name: 0 for name in beam_B_pins}
sequence_B = []

# =========================================================
# --- SD Card Setup ---
# =========================================================
spi = SPI(1, baudrate=config["spi"]["baudrate"], sck=Pin(config["spi"]["sck"]),
          mosi=Pin(config["spi"]["mosi"]), miso=Pin(config["spi"]["miso"]))
cs = Pin(config["spi"]["cs"], Pin.OUT)
det_pin = Pin(config["sd_detect_pin"], Pin.IN)
sd_present = False

source = "/Data"
destination = config["sd_destination"]

# =========================================================
# --- Buttons ---
# =========================================================
test_button_A = Pin(config["test_button_pin_A"], Pin.IN, Pin.PULL_UP)
test_button_B = Pin(config["test_button_pin_B"], Pin.IN, Pin.PULL_UP)
download_button = Pin(config["download_button_pin"], Pin.IN, Pin.PULL_UP)

last_test_state_A = 1
last_test_state_B = 1
last_download_state = 1
last_test_time_A = 0
last_test_time_B = 0
last_download_time = 0
DEBOUNCE_MS = config["download_debounce_ms"]

# =========================================================
# --- Logging ---
# =========================================================
def log_event(timestamp, pair, direction, set_label):
    file_name = file_name_A if set_label == "A" else file_name_B
    running = test_running_A if set_label == "A" else test_running_B
    if running and file_name:
        print(f"{timestamp} - {set_label} - {pair} - {direction}")
        with open(file_name, 'a') as f:
            f.write(f"{timestamp},{pair},{direction}\n")

# =========================================================
# --- Direction Detection ---
# =========================================================
def check_direction(sequence, set_label):
    if len(sequence) >= 2:
        first_gate, _ = sequence[0]
        second_gate, second_time = sequence[1]

        if first_gate.startswith("Left") and second_gate.startswith("Left"):
            direction = "Right" if first_gate.endswith("Left") else "Left"
            log_event(second_time, "Left Pair", direction, set_label)
        elif first_gate.startswith("Right") and second_gate.startswith("Right"):
            direction = "Right" if first_gate.endswith("Left") else "Left"
            log_event(second_time, "Right Pair", direction, set_label)

        sequence.clear()

# =========================================================
# --- Beam Gate Interrupts ---
# =========================================================
def make_gate_callback(name, sequence, last_trigger, set_label):
    def callback(pin):
        running = test_running_A if set_label == "A" else test_running_B
        if not running:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, last_trigger[name]) > DEBOUNCE:
            sequence.append((name, format_time(rtc.datetime())))
            check_direction(sequence, set_label)
            last_trigger[name] = now
    return callback

for name, pin in beam_A_pins.items():
    pin.irq(trigger=Pin.IRQ_FALLING, handler=make_gate_callback(name, sequence_A, last_trigger_A, "A"))

for name, pin in beam_B_pins.items():
    pin.irq(trigger=Pin.IRQ_FALLING, handler=make_gate_callback(name, sequence_B, last_trigger_B, "B"))

# =========================================================
# --- Test Control ---
# =========================================================
def start_new_test(set_label):
    global file_name_A, file_name_B, test_running_A, test_running_B
    dt = rtc.datetime()
    fname = f"{DATA_DIR}/{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}_{set_label}_{dt[4]:02}-{dt[5]:02}-{dt[6]:02}.csv"
    with open(fname, 'w') as f:
        f.write(f"Date:,{format_date(dt)}\n")
        f.write("Time,Pair,Direction\n")
    if set_label == "A":
        file_name_A = fname
        test_running_A = True
        status_led_A.value(1)
    else:
        file_name_B = fname
        test_running_B = True
        status_led_B.value(1)
    print(f"Started new test for Set {set_label}, logging to {fname}")

def stop_test(set_label):
    global test_running_A, test_running_B
    if set_label == "A":
        test_running_A = False
        status_led_A.value(0)
    else:
        test_running_B = False
        status_led_B.value(0)
    print(f"Test stopped for Set {set_label}, logging disabled")

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

def download_callback(pin):
    global sd_present, last_download_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_download_time) < DEBOUNCE_MS:
        return
    last_download_time = now

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
disconnect_delay = 500
last_all_high_time_A = time.ticks_ms()
last_all_high_time_B = time.ticks_ms()

while True:
    now = time.ticks_ms()

    # Test button A
    current_test_state_A = test_button_A.value()
    if last_test_state_A == 1 and current_test_state_A == 0:
        if time.ticks_diff(now, last_test_time_A) > DEBOUNCE_MS:
            if test_running_A:
                stop_test("A")
            else:
                start_new_test("A")
            last_test_time_A = now
    last_test_state_A = current_test_state_A

    # Test button B
    current_test_state_B = test_button_B.value()
    if last_test_state_B == 1 and current_test_state_B == 0:
        if time.ticks_diff(now, last_test_time_B) > DEBOUNCE_MS:
            if test_running_B:
                stop_test("B")
            else:
                start_new_test("B")
            last_test_time_B = now
    last_test_state_B = current_test_state_B

    # Download button
    current_download_state = download_button.value()
    if last_download_state == 1 and current_download_state == 0:
        if time.ticks_diff(now, last_download_time) > DEBOUNCE_MS:
            download_callback(None)
            last_download_time = now
    last_download_state = current_download_state

    # Module detection A
    states_A = [p.value() for p in beam_A_pins.values()]
    all_high_A = all(states_A)
    all_low_A = not any(states_A)
    if all_high_A:
        module_led_A.value(1)
        last_all_high_time_A = now
    elif all_low_A:
        if time.ticks_diff(now, last_all_high_time_A) > disconnect_delay:
            module_led_A.value(0)

    # Module detection B
    states_B = [p.value() for p in beam_B_pins.values()]
    all_high_B = all(states_B)
    all_low_B = not any(states_B)
    if all_high_B:
        module_led_B.value(1)
        last_all_high_time_B = now
    elif all_low_B:
        if time.ticks_diff(now, last_all_high_time_B) > disconnect_delay:
            module_led_B.value(0)

    time.sleep_ms(20)