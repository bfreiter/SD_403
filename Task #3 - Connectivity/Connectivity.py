from machine import ADC, Pin
import time

ldr = ADC(26)  # GP26 = ADC0

ledgreen = Pin(0, Pin.OUT)
ledgreen.off()

# Adjust this based on your ambient light conditions
threshold = 30000  

while True:
    value = ldr.read_u16()  # Range: 0-65535
    
    if value > threshold:
        ledgreen.on()
    else:
        ledgreen.off()
        
