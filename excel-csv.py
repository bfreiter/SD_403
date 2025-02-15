import machine
import utime
import os

# Define button A and button B pins (Active LOW)
button_A = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 15 for Button A
button_B = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)  # GPIO 14 for Button B

# Store power-up time
power_up_time = utime.time()

print("Waiting for button press...")

while True:
    # Initialize time variables for both buttons
    time_str_A = "-"
    time_str_B = "-"
    recorded = False  # Flag to indicate if any button has been pressed

    if button_A.value() == 0:  # Button A pressed (LOW)
        utime.sleep_ms(50)  # Debounce
        if button_A.value() == 0:  # Confirm still pressed
            elapsed_time_A = utime.time() - power_up_time
            
            # Convert to minutes and seconds if over 60 sec
            if elapsed_time_A >= 60:
                minutes_A = elapsed_time_A // 60
                seconds_A = elapsed_time_A % 60
                time_str_A = f"{minutes_A} min {seconds_A} sec"
            else:
                time_str_A = f"{elapsed_time_A} sec"

            print(f"Button A pressed after {time_str_A}")
            recorded = True  # Mark that Button A was pressed

            # Wait for button release to avoid duplicate logging
            while button_A.value() == 0:
                utime.sleep(0.1)

    if button_B.value() == 0:  # Button B pressed (LOW)
        utime.sleep_ms(50)  # Debounce
        if button_B.value() == 0:  # Confirm still pressed
            elapsed_time_B = utime.time() - power_up_time
            
            # Convert to minutes and seconds if over 60 sec
            if elapsed_time_B >= 60:
                minutes_B = elapsed_time_B // 60
                seconds_B = elapsed_time_B % 60
                time_str_B = f"{minutes_B} min {seconds_B} sec"
            else:
                time_str_B = f"{elapsed_time_B} sec"

            print(f"Button B pressed after {time_str_B}")
            recorded = True  # Mark that Button B was pressed

            # Wait for button release to avoid duplicate logging
            while button_B.value() == 0:
                utime.sleep(0.1)

    # Only write to CSV if either button was pressed
    if recorded:
        filename = "time_log.csv"
        write_header = filename not in os.listdir()
        
        with open(filename, "a") as file:
            if write_header:
                file.write("Elapsed Time Button A, Elapsed Time Button B\n")
            
            # Write the recorded time for each button in separate columns
            file.write(f"{time_str_A}, {time_str_B}\n")
            
        print(f"Time recorded: {time_str_A}, {time_str_B} in {filename}")
        

