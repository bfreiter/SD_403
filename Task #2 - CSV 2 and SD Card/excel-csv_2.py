import machine
from machine import Pin
import utime
import os
import ds3231  #For Real Time Clock (RTC)

#Setup LED's
ledred = Pin(0, Pin.OUT) #Red
ledgreen = Pin(1, Pin.OUT) #Green
ledred.off() #Reset LED's
ledgreen.off()

#Buttons used to simulate light gate triggers on either side
left = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 15
right = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 14

#Initialize I2C on Pico (GP16 = SDA and GP17 = SCL)to read RTC
i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16), freq=400000)

#Create DS3231 object (RTC)
rtc = ds3231.DS3231(i2c)

#Function for converting RTC data to string
def format_time(datetime_tuple):
    year, month, day, _, hour, minute, second, _ = datetime_tuple
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

#Read the time from the RTC
start_time = rtc.datetime()

#Take time for reference (Should be 01/01/2021)
startup = utime.time()

#Convert reference time to hours, minutes, and seconds
def convert_seconds(time_since):
    hours = time_since // 3600
    minutes = (time_since % 3600) // 60
    seconds = time_since % 60
    return hours, minutes, seconds

#Ensure the Data folder exists
if "Data" not in os.listdir():
    os.mkdir("Data")

#Initialize flags for file creation
rtc_file_created = False
no_rtc_file_created = False

#Loop Code
while True:
    #Set up default strings for CSV for each side
    left_string = ""
    right_string = ""
    
    #Initialize flags that check if a button has been pressed
    left_pressed = False
    right_pressed = False
    
    if start_time[0] > 2024:  #RTC available

        ledgreen.on()  #LED for testing
        
        if left.value() == 0:  #Left button pressed
            utime.sleep_ms(50)
            if left.value() == 0:  #Still pressed
                left_string = format_time(rtc.datetime())
                left_pressed = True
                
                while left.value() == 0:
                    utime.sleep_ms(100)

        if right.value() == 0:  #Right button pressed
            utime.sleep_ms(50)
            if right.value() == 0: 
                right_string = format_time(rtc.datetime())
                right_pressed = True
                
                while right.value() == 0:
                    utime.sleep_ms(500)

        #Write to csv file if a button was pressed
        if left_pressed or right_pressed:
            #Create the csv file if not already created
            if not rtc_file_created: #File name based off the time at startup
                file_name = f"Data/{start_time[0]}-{start_time[1]:02}-{start_time[2]:02}_{start_time[4]:02}-{start_time[5]:02}-{start_time[6]:02}.csv"
                with open(file_name, 'w') as file:
                    file.write("Left, Right\n")
                rtc_file_created = True
            
            with open(file_name, 'a') as file:
                file.write(f"{left_string}, {right_string}\n")    
    
    else:  #No RTC available for some reason
        ledred.on()  #Red LED

        if left.value() == 0:  #Left button pressed
            utime.sleep_ms(50)  #Debounce protection
            if left.value() == 0:  #Still pressed
                time_since_L = utime.time() - startup #Count time since startup
                left_time = convert_seconds(time_since_L) #Conver to readable time
                left_string = f"{left_time[0]:02}:{left_time[1]:02}:{left_time[2]:02}"
                left_pressed = True
                
                while left.value() == 0: #Debounce Protection
                    utime.sleep_ms(100)

        if right.value() == 0:  #Right button pressed
            utime.sleep_ms(50)
            if right.value() == 0: 
                time_since_R = utime.time() - startup
                right_time = convert_seconds(time_since_R)
                right_string = f"{right_time[0]:02}:{right_time[1]:02}:{right_time[2]:02}"
                right_pressed = True
                
                while right.value() == 0:
                    utime.sleep_ms(500)
        
        #Write to csv only if a button was pressed
        if left_pressed or right_pressed:
            #File created flag is false
            if no_rtc_file_created is False:
                #Get existing files in Data folder
                existing_files = os.listdir("Data")

                #Start from 0 and find the next available filename
                next_number = 0
                while f"No_Time_{next_number}.csv" in existing_files:
                    next_number += 1  #Increment until an available number is found

                #Filename
                no_rtc_filename = f"Data/No_Time_{next_number}.csv"

                #Create and write the file header if new
                with open(no_rtc_filename, 'w') as file:
                    file.write(""""Warning! An Error has occurred, No RTC Time Detected!"\nLeft, Right\n""")
                
                no_rtc_file_created = True  #Set flag to prevent recreation
            
            with open(no_rtc_filename, 'a') as file:
                file.write(f"{left_string}, {right_string}\n")