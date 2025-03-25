import serial
import time

# Open serial port (adjust port name as needed)
# On Linux it might be /dev/ttyUSB0 or /dev/ttyACM0
# On Windows it might be COM3, COM4, etc.
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  # Wait for connection to establish

def send_command(angle):
    command = f"S{angle}\n"
    ser.write(command.encode())
    print(f"Sent: {command.strip()}")
    # Read response
    response = ser.readline().decode().strip()
    if response:
        print(f"Response: {response}")

try:
    while True:
        angle = input("Enter steering angle (0-180): ")
        send_command(angle)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
1