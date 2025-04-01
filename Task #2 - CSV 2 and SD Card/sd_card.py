import machine
from machine import Pin
import sdcard
import os
import utime

download = machine.Pin(9, machine.Pin.IN, machine.Pin.PULL_UP) #Button to download Data from pico to SD
delete_pi = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP) #Button to clear pico Data folder

#Set LED's up
ledgreen = Pin(16, Pin.OUT)
ledred = Pin(17, Pin.OUT)
ledblue = Pin(18, Pin.OUT)
ledyellow = Pin(19, Pin.OUT)
ledgreen.off()
ledred.off()
ledblue.off()
ledyellow.off()

#SPI Bus 1, 1 MHz, Serial Clock - Pin 10, Master Out / Slave In - Pin 11, Master In / Slave Out - Pin 12
spi = machine.SPI(1, baudrate=1000000, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))
#Chip Select - Pin 13
cs = machine.Pin(13, machine.Pin.OUT)
#DET to detect SD card - Pin 14
det_pin = Pin(14, Pin.IN)

#Copy data from 'Data' folder in Pi Pico
source = "/Data"

#To 'Data' folder on SD Card
destination = "/sd/Data"

#SD Mounted Flag starts False
sd_present = False

#Function to try to mount the SD card
def mount_sd():
    global sd_present
    try: #Attemps to mount
        sd = sdcard.SDCard(spi, cs)  #Initialize SD Card Object
        vfs = os.VfsFat(sd)  #Create FAT File system object
        os.mount(vfs, "/sd")  #Try to mount SD card
        sd_present = True #SD Card is mounted
    except OSError: #If error occurs, not mounted
        sd_present = False

#Function for copying all folders
def copy_files(source, destination): #Takes source path, and destination path
    try:
        os.mkdir(destination)  #Create SD folder if it doesn’t exist
    except OSError:
        pass  #Ignores if folder exists

    #Find all items (files and folders) on pico
    for item in os.listdir(source):
        source_path = "{}/{}".format(source, item) #Source path
        destination_path = "{}/{}".format(destination, item) #Destination path

        if os.stat(source_path)[0] & 0x4000:  #Item is a folder
            copy_files(source_path, destination_path)  #Copy subfolder
        else: #Item is a file
            #Open source in binary read mode and destination as binary write mode
            with open(source_path, 'rb') as fsource, open(destination_path, 'wb') as fdestination:
                while True: #Loops until entire file copied
                    ledblue.on() #Blinks Blue LED
                    buf = fsource.read(1024)  #Copies in chunks of 1024 Bytes (1KB)
                    utime.sleep_ms(100)
                    ledblue.off()
                    if not buf: #End of file
                        break #Exit Loop
                    fdestination.write(buf) #Writes to SD file

#Function to delete all files inside the 'Data' folder on pico
def delete_pico_Data(folder):
    try:
        #Find all items (files and folders) on pico 
        for item in os.listdir(folder):
            path = "{}/{}".format(folder, item) #File Path
            if os.stat(path)[0] & 0x4000:  #Item is a folder
                delete_pico_Data(path)  #Delete 'Data' folder contents
            else: #Item is a file
                os.remove(path) #Deletes file
    except OSError:
        pass #Folder exists or is empty

#Main loop
while True:
    if det_pin.value() == 1: #SD inserted
        ledgreen.on()
        ledred.off()
    else: #SD not inserted
        ledred.on()
        ledgreen.off()

    #Check if SD is not mounted, try again
    if not sd_present:
        mount_sd()

    #Delete files from pico/Data
    if delete_pi.value() == 0:
        utime.sleep_ms(50)  #Debounce protection
        if delete_pi.value() == 0:  #Button still pressed
            delete_pico_Data(source) #Delete 'Data' function
            #Flash blue LED for successful delete
            for i in range(5):
                ledblue.on()
                utime.sleep_ms(100)
                ledblue.off()
                utime.sleep_ms(100)

            #Debounce wait for button release
            while delete_pi.value() == 0:
                utime.sleep_ms(100)

    #Copy files to SD
    if download.value() == 0:
        utime.sleep_ms(50)  #Debounce protection
        if download.value() == 0:  #Button still pressed
            if sd_present:
                try:
                    if os.stat(source)[0] & 0x4000:  #Ensure 'Data' is a directory
                        copy_files(source, destination) #Copy files from pico to SD
                except OSError: #Folder not found, skip
                    pass

                #Safely unmount SD card after transfer
                os.umount("/sd")

                ledgreen.off() #Indicate with  LED
                ledred.on()
                
                #Flash yellow to show SD needs to be removed
                while det_pin.value() == 1:
                    ledyellow.on()
                    utime.sleep_ms(500)
                    ledyellow.off()
                    utime.sleep_ms(500)

                sd_present = False  #Reset flag to allow remounting

            #Debounce wait for button release
            while download.value() == 0:
                utime.sleep_ms(100)