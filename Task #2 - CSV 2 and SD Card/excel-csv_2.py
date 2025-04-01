import machine
from machine import Pin
import utime
import os
import ds3231  #For Real Time Clock (RTC)

#Setup LED's
ledgreen = Pin(0, Pin.OUT) #Red
ledred = Pin(1, Pin.OUT) #Green
ledblue = Pin(2, Pin.OUT) #Red
ledyellow = Pin(3, Pin.OUT) #Green
ledgreen.off() #Reset LED's
ledred.off()
ledblue.off()
ledyellow.on()

#Buttons used to simulate light gate triggers on either side
start_test = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 15
end_test = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 14

left_in = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 15
left_out = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 15

right_in = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 15
right_out = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_UP)  #GPIO 15

#Initialize I2C on Pico (GP16 = SDA and GP17 = SCL)to read RTC
i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16), freq=400000)

#Create DS3231 object (RTC)
rtc = ds3231.DS3231(i2c)

#Function for converting RTC data to string
def format_time(datetime_tuple):
    year, month, day, _, hour, minute, second, _ = datetime_tuple
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

#Convert reference time to hours, minutes, and seconds
def convert_seconds(time_since):
    hours = time_since // 3600
    minutes = (time_since % 3600) // 60
    seconds = time_since % 60
    return hours, minutes, seconds

def calculate_elapsed_time(start, end):
    t1 = start[4] * 3600 + start[5] * 60 + start[6]
    t2 = end[4] * 3600 + end[5] * 60 + end[6]
    elapsed_seconds = convert_seconds(t2 - t1)
    return f"{elapsed_seconds[0]:02}:{elapsed_seconds[1]:02}:{elapsed_seconds[2]:02}"

#Ensure the Data folder exists
if "Data" not in os.listdir():
    os.mkdir("Data")

#Initialize flags for file creation
rtc_file_created = False
row = 1

left_entry_time = None
right_entry_time = None

started = False

test_rtc = rtc.datetime()

#Loop Code
while True:
    if test_rtc[0] > 2024:  #RTC available
        ledgreen.on()  #LED for testing
        ledred.off()
    else:
        ledred.on()  #LED for testing
        ledgreen.off()

    if not started:
        if start_test.value() == 0:
            utime.sleep_ms(50)
            if start_test.value() == 0:
                started = True
                #Read the time from the RTC
                start_time = rtc.datetime()
                rtc_file_created = False
                ledyellow.off()
                ledblue.on()
    
    while started:
        #Set up default strings for CSV for each side
        left_in_string = ""
        right_in_string = ""
        left_out_string = ""
        right_out_string = ""
        left_time_string = ""
        right_time_string = ""
        
        if end_test.value() == 0:
            utime.sleep_ms(50)
            if end_test.value() == 0:
                started = False
                ledyellow.on()
                ledblue.off()
                break
    
        if start_time[0] > 2024:  #RTC available        
            if left_in.value() == 0:  #Left button pressed
                utime.sleep_ms(50)
                if left_in.value() == 0:  #Still pressed
                    left_entry_time = rtc.datetime()
                    while left_in.value() == 0:
                        utime.sleep_ms(100)

            if left_out.value() == 0 and left_entry_time:  #Left button pressed
                utime.sleep_ms(50)
                if left_out.value() == 0: 
                    left_exit_time = rtc.datetime()
                    left_time_string = calculate_elapsed_time(left_entry_time, left_exit_time)
                    left_in_string = format_time(left_entry_time)  # Format RTC time for display
                    left_out_string = format_time(left_exit_time)  # Format RTC time for display
                    left_entry_time = None                   
                    while left_out.value() == 0:
                        utime.sleep_ms(100)
                        
            if right_in.value() == 0:  #Left button pressed
                utime.sleep_ms(50)
                if right_in.value() == 0:  #Still pressed
                    right_entry_time = rtc.datetime()
                    while right_in.value() == 0:
                        utime.sleep_ms(100)

            if right_out.value() == 0 and right_entry_time:  #Left button pressed
                utime.sleep_ms(50)
                if right_out.value() == 0: 
                    right_exit_time = rtc.datetime()
                    right_time_string = calculate_elapsed_time(right_entry_time, right_exit_time)
                    right_in_string = format_time(right_entry_time)  # Format RTC time for display
                    right_out_string = format_time(right_exit_time)  # Format RTC time for display
                    right_entry_time = None                   
                    while right_out.value() == 0:
                        utime.sleep_ms(100)

            # Write to CSV if any data recorded
            if left_in_string or right_in_string:
                if not rtc_file_created:
                    file_name = f"Data/{start_time[0]}-{start_time[1]:02}-{start_time[2]:02}_{start_time[4]:02}-{start_time[5]:02}-{start_time[6]:02}.csv"
                    with open(file_name, 'w') as file:
                        file.write("#, Entered Left, Exited Left, Time Left, Entered Right, Exited Right, Time Right\n")
                    rtc_file_created = True

                with open(file_name, 'a') as file:
                    file.write(f"{row}, {left_in_string}, {left_out_string}, {left_time_string}, {right_in_string}, {right_out_string}, {right_time_string}\n")
                    row += 1
        else:
            break