import machine
import ds3231
import utime

# Initialize I2C on Pico (GP20 = SDA, GP21 = SCL)
i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16), freq=400000)

# Create DS3231 object
rtc = ds3231.DS3231(i2c)

# Set the time only once (adjust to your current time)
# Format: (year, month, day, weekday, hour, minute, second)
# Example: Set to 2025-02-17 14:30:00
rtc.datetime((2025, 3, 18, 8, 9, 58, 0))  # Set current date and time

# Print the time to confirm
while True:
    current_time = rtc.datetime()
    readable_time = f"{current_time[0]:04d}-{current_time[1]:02d}-{current_time[2]:02d} {current_time[4]:02d}:{current_time[5]:02d}:{current_time[6]:02d}"
    print("Current Time:", readable_time)
    utime.sleep(1)