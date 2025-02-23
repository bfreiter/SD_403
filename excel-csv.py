import machine
from machine import Pin
import utime
import os

### Test LED's ###
ledred = Pin(1, Pin.OUT)
ledgreen = Pin(2, Pin.OUT)
ledred.off()
ledgreen.off()

# Define Pins to represent left or right sides
left = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 15
right = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 14

# Directory paths for storing CSV files
parent_directory = "Data"
no_startup_directory = "No_Startup"
startup_directory = "Startup"

# Checks what the startup time is, epoch integer
startup_time = utime.time()

# Create the parent directory if it doesn't exist
if parent_directory not in os.listdir():
    os.mkdir(parent_directory)

# Create the No_Startup and Startup directories inside the Data folder
if startup_time == 1609459201:
    no_startup_path = f"{parent_directory}/{no_startup_directory}"
    if no_startup_directory not in os.listdir(parent_directory):
        os.mkdir(no_startup_path)

startup_path = f"{parent_directory}/{startup_directory}"
if startup_directory not in os.listdir(parent_directory):
    os.mkdir(startup_path)

# Function to Determine Time in Readable Format
def readable_time(epoch_int):
    r_time = utime.localtime(epoch_int)  # Convert a time expressed in seconds since the Epoch into an 8-tuple
    year = r_time[0]
    month = r_time[1]
    day = r_time[2]
    hour = r_time[3]
    minute = r_time[4]
    second = r_time[5]
    
    return year, month, day, hour, minute, second

year, month, day, hour, minute, second = readable_time(startup_time)  # Integer Values for all time components

start_time_string_total = f"{month:02}/{day:02}/{year:02}_{hour:02}:{minute:02}:{second:02}"

#***Only for Case when no startup time detected
def filename_int_no_startup(directory):
    count = 0 #First File has integer 0
    while True:
        filename_no_startup = f"data_{count}.csv" #Adjust File Name if it already exists
        if filename_no_startup not in os.listdir(directory): #Check if it exists in the directory
            return filename_no_startup
        count += 1

warning_message = "***Warning, no time was detected at start up. All time values are since device was turned on.***"

file_created = False
filename_no_startup = ""
#***

# Loop Code
while True:
    # Set up default strings for CSV for each side
    left_string = ""
    right_string = ""
    press = False  # Button needs to be pressed for CSV writing
    
    if startup_time == 1609459201:  # Therefore, do not have the actual time, have the default
        ledred.on()  # LED for testing
        
        if left.value() == 0:  # Left button pressed
            utime.sleep_ms(50)  # Debounce protection
            if left.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                time_since_L = utime.time() - startup_time  # Find the time since startup
                
                # Display time in appropriate format
                hours_L = time_since_L // 3600
                minutes_L = (time_since_L % 3600) // 60
                seconds_L = time_since_L % 60
                left_string = f"{hours_L:02}:{minutes_L:02}:{seconds_L:02}"
                
                # Wait until button is released
                while left.value() == 0:
                    utime.sleep_ms(500)
               

        if right.value() == 0:  # Right button pressed
            utime.sleep_ms(50)  # Debounce protection
            if right.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                time_since_R = utime.time() - startup_time  # Find the time since startup
                
                hours_R = time_since_R // 3600
                minutes_R = (time_since_R % 3600) // 60
                seconds_R = time_since_R % 60
                right_string = f"{hours_R:02}:{minutes_R:02}:{seconds_R:02}"
                
                # Wait until button is released
                while right.value() == 0:
                    utime.sleep_ms(500)
    

        if press and not file_created:
            # Get the next available filename in the No_Startup directory
            filename_no_startup = filename_int_no_startup(no_startup_path)

            # Open the file in the specified directory and write the header
            with open(f"{no_startup_path}/{filename_no_startup}", "a") as file:
                file.write(f"{warning_message}\nElapsed Time Left, Elapsed Time Right\n")
            
            # Set the flag to prevent creating the file again
            file_created = True

        # Write the data to the file after the first button press
        if press and file_created:
            with open(f"{no_startup_path}/{filename_no_startup}", "a") as file:
                file.write(f"{left_string}, {right_string}\n")
    else:
        ledgreen.on()
        
        if left.value() == 0:  # Left button pressed
            utime.sleep_ms(50)  # Debounce protection
            if left.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                year, month, day, hour, minute, second = readable_time(utime.time())
                time_string_no_date = f"{hour:02}:{minute:02}:{second:02}"
                
                left_string = time_string_no_date
                
                # Wait until button is released
                while left.value() == 0:
                    utime.sleep_ms(500)
               

        if right.value() == 0:  # Right button pressed
            utime.sleep_ms(50)  # Debounce protection
            if right.value() == 0:  # Still pressed
                press = True  # Button pressed, allow CSV to write
                year, month, day, hour, minute, second = readable_time(utime.time())
                time_string_no_date = f"{hour:02}:{minute:02}:{second:02}"
                
                right_string = time_string_no_date
                
                # Wait until button is released
                while right.value() == 0:
                    utime.sleep_ms(500)
        
        if press and not file_created:
            # Create the unique filename with timestamp for the file (including seconds) in Startup directory
            timestamp = f"{month:02}-{day:02}-{year:02}_{hour:02}-{minute:02}-{second:02}"
            filename_with_time = f"{timestamp}.csv"
            
            # Open the file in the "Startup" directory and write the header
            with open(f"{startup_path}/{filename_with_time}", "w") as file:  # Use "w" to create a new file
                file.write(f"Time Detected at Startup:, {start_time_string_total}\nTime Left, Time Right\n")
            
            # Set the flag to prevent creating the file again
            file_created = True

        # Write the data to the file after the first button press
        if press and file_created:
            with open(f"{startup_path}/{filename_with_time}", "a") as file:  # Use "a" to append data
                file.write(f"{left_string}, {right_string}\n")

