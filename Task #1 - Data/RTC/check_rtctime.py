import machine
import ds3231
import utime

# Initialize I2C on Pico (GP20 = SDA, GP21 = SCL)
i2c = machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20), freq=400000)

# Create DS3231 object
rtc = ds3231.DS3231(i2c)

def format_time(datetime_tuple):
    # Extract datetime tuple: (year, month, day, weekday, hour, minute, second, century_flag)
    year, month, day, weekday, hour, minute, second, _ = datetime_tuple  # Ignore the century flag
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

# Read and print the time

current_time = rtc.datetime()


print(format_time(current_time))


