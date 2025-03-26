import machine
from machine import Pin
import sdcard
import os
import utime

download = machine.Pin(9, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 9

ledgreen = Pin(16, Pin.OUT)  # Green LED
ledred = Pin(17, Pin.OUT)
ledblue = Pin(18, Pin.OUT)
ledyellow = Pin(19, Pin.OUT)
ledgreen.off()
ledred.off()
ledblue.off()
ledyellow.off()

#SPI Bus 1, 1 MHz, Serial Clock - Pin 10, Master Out / Slave In - Pin 11, Master In / Slave Out - Pin 12
spi = machine.SPI(1, baudrate=1000000, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))
# Chip Select - Pin 13
cs = machine.Pin(13, machine.Pin.OUT)
# DET pin to detect SD card insertion
det_pin = Pin(14, Pin.IN)  # GPIO 14 for DET pin

# Copy data from Data folder in Pi Pico
src_dir = "/Data"
# To Corresponding folder on SD Card
dst_dir = "/sd/Data"

# Check if SD card is mounted
sd_present = False

# Function to attempt mounting the SD card
def mount_sd():
    global sd_present
    try:
        sd = sdcard.SDCard(spi, cs)  # Initialize SD Card Object
        vfs = os.VfsFat(sd)  # Create FAT File system object
        os.mount(vfs, "/sd")  # Try to mount SD card
        sd_present = True
    except OSError:
        sd_present = False

# Function for copying all folders
def copy_folder(src, dst):
    try:
        os.mkdir(dst)  # Create destination folder if it doesn’t exist
    except OSError:
        pass # Ignore if folder already exists

    # Find all files and folders
    for item in os.listdir(src):
        src_path = "{}/{}".format(src, item)  # Source Folder (Data)
        dst_path = "{}/{}".format(dst, item)  # Destination (SD Card)

        if os.stat(src_path)[0] & 0x4000:  # Check if item is a folder
            copy_folder(src_path, dst_path)  # Copy subfolder
        else:
            # Open source in binary read and destination as binary write
            with open(src_path, 'rb') as fsrc, open(dst_path, 'wb') as fdst:
                while True:
                    ledblue.on()
                    buf = fsrc.read(1024)  # Copies in chunks of 1024 Bytes
                    utime.sleep_ms(100)
                    ledblue.off()
                    if not buf:
                        break
                    fdst.write(buf)
            print(f"Copied {src_path} → {dst_path}")

# Main loop
while True:
    if det_pin.value() == 1:
        ledgreen.on()
        ledred.off()
    else:
        ledred.on()
        ledgreen.off()
        
    # Check if SD card is not mounted, try mounting it again
    if not sd_present:
        mount_sd()

    # If the button is pressed
    if download.value() == 0:
        utime.sleep_ms(50)  # Debounce protection
        if download.value() == 0:  # Still pressed
            if sd_present:
                try:
                    if os.stat(src_dir)[0] & 0x4000:  # Ensure 'Data' is a directory
                        print(f"Transferring '{src_dir}' to SD card...")
                        copy_folder(src_dir, dst_dir)
                        print("Transfer complete!")
                    else:
                        print("Error: 'Data' exists but is not a folder!")
                except OSError:
                    print("No 'Data' folder found. Skipping transfer.")
                
                # Safely unmount SD card after transfer
                os.umount("/sd")
                print("SD Card safely unmounted.")
                
                ledgreen.off()
                ledred.on()
                
                while det_pin.value() == 1:
                    ledyellow.on()
                    utime.sleep_ms(500)
                    ledyellow.off()
                    utime.sleep_ms(500)
                
                sd_present = False  # Reset flag to allow remounting later
                        
            # Debounce protection for button release
            while download.value() == 0:
                utime.sleep_ms(100)
