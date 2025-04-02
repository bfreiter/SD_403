import machine
from machine import Pin
import utime
import os
import ds3231  #For Real Time Clock (RTC)

#Setup LED's
ledgreen = Pin(0, Pin.OUT) #Red
ledred = Pin(1, Pin.OUT) #Green
ledblue = Pin(2, Pin.OUT) #Blue
ledyellow = Pin(3, Pin.OUT) #Yellow
ledgreen.off() #Reset LED's
ledred.off()
ledblue.off()
ledyellow.on()

start_test = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP) #Button to begin a test
end_test = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP) #Button to end a test

left_in = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP) #Button for entering left side
left_out = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP) #Button for exiting left side

right_in = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_UP) #Button for entering right side
right_out = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_UP) #Button for exiting right side

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

#Determine the elapsed time spent on a side
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

left_entry_time = None
right_entry_time = None

started = False

#Testing to see if rtc is accurate
test_rtc = rtc.datetime()

#Main Loop
while True:
    if test_rtc[0] > 2024: #RTC available
        ledgreen.on()
        ledred.off()
    else: #RTC not available
        ledred.on()  
        ledgreen.off()
    
    #Wait for start button to be pressed
    if not started:
        if start_test.value() == 0: #Start pressed
            utime.sleep_ms(50)
            if start_test.value() == 0: #Still pressed
                started = True #Set flag
                start_time = rtc.datetime() #Read the time from the RTC
                rtc_file_created = False #Reset flag, ensure new csv can be created
                ledyellow.off() #LED's
                ledblue.on()
    
    while started:
        #Set up default strings for CSV
        left_in_string = ""
        right_in_string = ""
        left_out_string = ""
        right_out_string = ""
        left_time_string = ""
        right_time_string = ""
        
        #Wait for end button to be pressed
        if end_test.value() == 0: #End pressed
            utime.sleep_ms(50)
            if end_test.value() == 0: #Still pressed
                started = False #Set Flag
                ledyellow.on() #LED's
                ledblue.off()
                break
    
        if start_time[0] > 2024:  #RTC available        
            if left_in.value() == 0:  #Left button pressed
                utime.sleep_ms(50)
                if left_in.value() == 0:  #Still pressed
                    left_entry_time = rtc.datetime() #Record entry time
                    while left_in.value() == 0:
                        utime.sleep_ms(100)

            if left_out.value() == 0 and left_entry_time: #Exit button pressed, and enter button previously pressed
                utime.sleep_ms(50)
                if left_out.value() == 0: 
                    left_exit_time = rtc.datetime() #Record exit time
                    left_time_string = calculate_elapsed_time(left_entry_time, left_exit_time) #Calculate time spent
                    left_in_string = format_time(left_entry_time)  #Format RTC for display
                    left_out_string = format_time(left_exit_time)  #Format RTC for display
                    left_entry_time = None #Reset entry time                   
                    while left_out.value() == 0:
                        utime.sleep_ms(100)
                        
            if right_in.value() == 0:  #Right button pressed
                utime.sleep_ms(50)
                if right_in.value() == 0:  #Still pressed
                    right_entry_time = rtc.datetime() #Record entry time
                    while right_in.value() == 0:
                        utime.sleep_ms(100)

            if right_out.value() == 0 and right_entry_time: #Exit button pressed, and enter button previously pressed
                utime.sleep_ms(50)
                if right_out.value() == 0: 
                    right_exit_time = rtc.datetime() #Record exit time
                    right_time_string = calculate_elapsed_time(right_entry_time, right_exit_time) #Calculate time spent
                    right_in_string = format_time(right_entry_time)  #Format RTC for display
                    right_out_string = format_time(right_exit_time)  #Format RTC for display
                    right_entry_time = None #Reset entry time                    
                    while right_out.value() == 0:
                        utime.sleep_ms(100)

            #Write to CSV if any data recorded
            if left_in_string or right_in_string:
                if not rtc_file_created: #Create RTC if not already created
                    file_name = f"Data/{start_time[0]}-{start_time[1]:02}-{start_time[2]:02}_{start_time[4]:02}-{start_time[5]:02}-{start_time[6]:02}.csv" #Name it after the time test started at
                    #Initialize row for CSV
                    row = 1
                    with open(file_name, 'w') as file: #Write to the new CSV
                        file.write("#, Entered Left, Exited Left, Time Left, Entered Right, Exited Right, Time Right\n") #Create the column titles
                    rtc_file_created = True #Set Flag

                with open(file_name, 'a') as file: #Add onto CSV file
                    file.write(f"{row}, {left_in_string}, {left_out_string}, {left_time_string}, {right_in_string}, {right_out_string}, {right_time_string}\n") #Write all relevant data to CSV
                    row += 1 #Increment row of CSV
        else:
            break