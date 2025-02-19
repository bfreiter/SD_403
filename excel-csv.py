import machine
from machine import Pin
import utime
import os

###Test LED's###
led1 = Pin(1, Pin.OUT)
led2 = Pin(2, Pin.OUT)
led1.off()
led2.off()

#Define Pins to represent left or right sides
left = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP) #GPIO 15
right = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP) #GPIO 14

#Checks what the startup time is, epoch integer
startup_time = utime.time()

#Loop Code
while True:
    #Set up default strings for csv for each side
    left_string = "-"
    right_string = "-"
    press = False #Button needs to be pressed for csv writing
    
    if startup_time == 1609459201: #Therefore, do not have the actual time, have the default
        
        led1.on() #Led for testing
        
        if left.value() == 0: #Left button pressed
            utime.sleep_ms(50) #Debounce protection
            if left.value() == 0: #Still pressed
                press = True #Button pressed, allow csv to write
                time_since_L = utime.time() - startup_time #Find the time since startup
                
                #Display time in appropriate format
                minutes_L = time_since_L // 60
                seconds_L = time_since_L % 60
                left_string = str(minutes_L) + " min " + str(seconds_L) + " sec"
                
                #Wait until button is released
                while left.value() == 0:
                    utime.sleep_ms(500)
               
        if right.value() == 0: #Left button pressed
            utime.sleep_ms(50) #Debounce protection
            if right.value() == 0: #Still pressed
                press = True #Button pressed, allow csv to write
                time_since_R = utime.time() - startup_time #Find the time since startup
                
                #Display time in appropriate format
                minutes_R = time_since_R // 60
                seconds_R = time_since_R % 60
                right_string = str(minutes_R) + " min " + str(seconds_R) + " sec"
                
                #Wait until button is released
                while right.value() == 0:
                    utime.sleep_ms(500)
        
        #****Left Off
        if press:
            filename = "time_log.csv"
            write_header = filename not in os.listdir()
        
            with open(filename, "a") as file:
                if write_header:
                    file.write("Elapsed Time Left Button, Elapsed Time Right Button\n")
            
                # Write the recorded time for each button in separate columns
                file.write(f"{left_string}, {right_string}\n")
                            
    else:
        led2.on()   
        


