from machine import ADC, Pin
import utime

#Setup LDR's on A/D pins
ldr_1 = ADC(26) 
ldr_2 = ADC(27)

#Setup LEd's
ledgreen = Pin(0, Pin.OUT)
ledgreen.off()
ledblue = Pin(2, Pin.OUT)
ledblue.off()

#Define Threshold that voltage (0-65536)
threshold = 35000  #Voltage threshold that corresponds to LDR value when LED on
on_time = 1000  #Must be plugged in for 1 second (1000ms) before gate considered connected (avoids misreads)

#Track how long the input has been above threshold
timer_1 = 0
timer_2 = 0

#Main Loop
while True:
    ad_1 = ldr_1.read_u16() #Reads A/D value for LDR_1
    ad_2 = ldr_2.read_u16() #Reads A/D value for LDR_2
    
    if ad_1 > threshold: #If the A/D value is higher than threshold, LED should be on
        timer_1 += 50 #Start adding 50 ms (main loop execution time)
        if timer_1 >= on_time: #1 second has elapsed
            ledgreen.on() #Turn on green LED, indicating a module was connected
    else: #Once A/D value goes below threshold, turn off LED (prevents accidentally thinking gate connected)
        timer_1 = 0
        ledgreen.off()
        
    if ad_2 > threshold: #If the A/D value is higher than threshold, LED should be on
        timer_2 += 50 #Start adding 50 ms (main loop execution time)
        if timer_2 >= on_time: #1 second has elapsed
            ledblue.on() #Turn on green LED, indicating a module was connected
    else: #Once A/D value goes below threshold, turn off LED (prevents accidentally thinking gate connected)
        timer_2 = 0
        ledblue.off()

    utime.sleep_ms(50) #Loop every 50ms
