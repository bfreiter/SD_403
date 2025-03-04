import machine
from machine import Pin
import utime
import os
import ds3231 #For RTC

### Test LED's ###
ledred = Pin(0, Pin.OUT)
ledgreen = Pin(1, Pin.OUT)
ledred.off()
ledgreen.off()

#Buttons used to simulate light gate triggers on either sides
left = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 15
right = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 14

#Initialize I2C on Pico (GP20 = SDA, GP21 = SCL)
i2c = machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20), freq=400000)

#Create DS3231 object
rtc = ds3231.DS3231(i2c)

#Function for converting RTC data to string
def format_time(datetime_tuple):
    # Extract datetime tuple: (year, month, day, weekday, hour, minute, second, century_flag)
    year, month, day, weekday, hour, minute, second, _ = datetime_tuple  # Ignore the century flag
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

#Read the time from the RTC
start_time = rtc.datetime()

#Take time for reference
startup = utime.time()
#Convert reference time to 
def convert_seconds(time_since):
    hours = time_since // 3600
    minutes = (time_since % 3600) // 60
    seconds = time_since % 60
    return hours, minutes, seconds

# Loop Code
while True:
    # Set up default strings for CSV for each side
    left_string = ""
    right_string = ""
    press = False  # Button needs to be pressed for CSV writing
    
    if start_time[0] < 2024: #Do not have RTC time
        ledred.on()  #LED for testing
        
        if left.value() == 0:  # Left button pressed
            utime.sleep_ms(50)  # Debounce protection
            if left.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                time_since_L = utime.time() - startup # Find the time since startup
            
                # Display time in appropriate format
                left_time = convert_seconds(time_since_L)
                
                left_string = f"{left_time[0]:02}:{left_time[1]:02}:{left_time[2]:02}"
                
                # Wait until button is released
                
                while left.value() == 0:
                    utime.sleep_ms(100)
               

        if right.value() == 0:  # Right button pressed
             utime.sleep_ms(50)  # Debounce protection
             if right.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                time_since_R = utime.time() - startup  # Find the time since startup
                
                right_time = convert_seconds(time_since_R)
                
                right_string = f"{right_time[0]:02}:{right_time[1]:02}:{right_time[2]:02}"
                
                # Wait until button is released
                while right.value() == 0:
                    utime.sleep_ms(500)
                    
    else: #Do not have RTC time
        ledgreen.on()  #LED for testing
        
        if left.value() == 0:  # Left button pressed
            utime.sleep_ms(50)  # Debounce protection
            if left.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                
                left_string = format_time(rtc.datetime())

                # Wait until button is released
                
                while left.value() == 0:
                    utime.sleep_ms(100)

        if right.value() == 0:  # Right button pressed
             utime.sleep_ms(50)  # Debounce protection
             if right.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                time_since_R = utime.time() - startup  # Find the time since startup
            
                right_string = format_time(rtc.datetime())

                # Wait until button is released
                while right.value() == 0:
                    utime.sleep_ms(500)