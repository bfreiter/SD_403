import time
import uos

# Get the current timestamp (seconds since epoch)
timestamp = time.time()

# Convert the timestamp to a struct_time object
local_time = time.localtime(timestamp)

# Manually format the time (Year-Month-Day Hour:Minute:Second)
formatted_time = f"{local_time[0]}-{local_time[1]:02d}-{local_time[2]:02d} {local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d}"

# Open CSV file in write mode on the internal storage
with open('startup_time.csv', 'w') as file:
    # Write headers for the CSV
    file.write("Formatted Timestamp\n")
    
    # Write the formatted time to the CSV file
    file.write(f"{formatted_time}\n")

# Print confirmation to the console
print(f"Startup time has been recorded to startup_time.csv: {formatted_time}")
