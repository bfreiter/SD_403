import machine
import sdcard
import os

# ======= SPI & SD Card Setup ======= #
spi = machine.SPI(1, baudrate=1000000, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))
cs = machine.Pin(13, machine.Pin.OUT)
sd = sdcard.SDCard(spi, cs)
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# ======= Source and Destination Paths ======= #
src_dir = "/Data"  # Source folder on Pico
dst_dir = "/sd/Data"  # Destination folder on SD card

# ======= Function to Copy a Full Folder Recursively ======= #
def copy_folder(src, dst):
    """ Recursively copies a folder and its contents to the SD card. """
    try:
        os.mkdir(dst)  # Create destination folder if it doesn’t exist
    except OSError:
        pass  # Ignore if folder already exists

    for item in os.listdir(src):
        src_path = "{}/{}".format(src, item)
        dst_path = "{}/{}".format(dst, item)

        if os.stat(src_path)[0] & 0x4000:  # Check if item is a folder
            copy_folder(src_path, dst_path)  # Recursively copy subfolder
        else:
            with open(src_path, 'rb') as fsrc, open(dst_path, 'wb') as fdst:
                while True:
                    buf = fsrc.read(1024)
                    if not buf:
                        break
                    fdst.write(buf)
            print(f"Copied {src_path} → {dst_path}")

# ======= Check if Source Folder Exists Properly ======= #
try:
    if os.stat(src_dir)[0] & 0x4000:  # Ensure 'Data' is a directory
        print(f"Transferring '{src_dir}' to SD card...")
        copy_folder(src_dir, dst_dir)
        print("Transfer complete!")
    else:
        print("Error: 'Data' exists but is not a folder!")
except OSError:
    print("No 'Data' folder found. Exiting.")

# ======= Unmount the SD Card (Optional) ======= #
os.umount("/sd")
print("SD Card safely unmounted.")
