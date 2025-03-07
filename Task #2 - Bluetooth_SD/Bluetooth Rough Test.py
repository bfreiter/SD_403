import bluetooth
import time
from machine import Pin
from ble_simple_peripheral import BLESimplePeripheral

led = Pin(25, Pin.OUT)  # Onboard LED for status indication

# Initialize BLE
ble = bluetooth.BLE()
peripheral = BLESimplePeripheral(ble, name="Pico-BLE")

print("Bluetooth Peripheral Initialized. Waiting for connections...")

while True:
    if peripheral.is_connected():
        print("Device connected!")
        led.on()
        time.sleep(1)
        peripheral.send("Hello from Pi Pico!")  # Send test message
    else:
        led.off()
        print("Waiting for connection...")
    time.sleep(5)
