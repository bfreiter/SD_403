import machine
import sdcard
import os

#SPI Bus 1, 1 MHz, Serial Clock - Pin 10, Master Out / Slave In - Pin 11, Master In / Slave Out - Pin 12
spi = machine.SPI(1, baudrate=1000000, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))
#Chip Select - Pin 13
cs = machine.Pin(13, machine.Pin.OUT)
#Initialize to SPI, and create SD Card Object
sd = sdcard.SDCard(spi, cs)
#FAT File system object creation
vfs = os.VfsFat(sd)
#Access in directory /sd
os.mount(vfs, "/sd")

#Copy data from Data folder in Pi Pico
src_dir = "/Data"
#To Corresponding folder on SD Card
dst_dir = "/sd/Data"

#Function for copying all folders
def copy_folder(src, dst):
    try:
        os.mkdir(dst)  #Create destination folder if it doesn’t exist
    except OSError:
        pass  #Ignore if folder already exists
    
    #Find all files and folders
    for item in os.listdir(src):
        src_path = "{}/{}".format(src, item) #Source Folder (Data)
        dst_path = "{}/{}".format(dst, item) #Destination (SD Card)

        if os.stat(src_path)[0] & 0x4000:  #Check if item is a folder
            copy_folder(src_path, dst_path)  #Copy subfolder
        else:
            #Open spurce in binary read, and destination as binary right
            with open(src_path, 'rb') as fsrc, open(dst_path, 'wb') as fdst:
                while True:
                    #Copies in chunks of 1024 Bytes
                    buf = fsrc.read(1024)
                    if not buf:
                        break
                    fdst.write(buf)
            print(f"Copied {src_path} → {dst_path}")

#Checks if the source directory exists, print information
try:
    if os.stat(src_dir)[0] & 0x4000:  # Ensure 'Data' is a directory
        print(f"Transferring '{src_dir}' to SD card...")
        copy_folder(src_dir, dst_dir)
        print("Transfer complete!")
    else:
        print("Error: 'Data' exists but is not a folder!")
except OSError:
    print("No 'Data' folder found. Exiting.")

#Don't corrupt data
os.umount("/sd")
print("SD Card safely unmounted.")
