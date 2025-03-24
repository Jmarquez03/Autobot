#!/usr/bin/env python3
from gpiozero import AngularServo
import time
import argparse

def test_servo(gpio_pin=17, min_pw=0.5, max_pw=2.5, min_angle=0, max_angle=120):
    """
    Test a servo motor using gpiozero
    
    Args:
        gpio_pin: GPIO pin number (BCM numbering)
        min_pw: Minimum pulse width in milliseconds
        max_pw: Maximum pulse width in milliseconds
        min_angle: Minimum angle in degrees
        max_angle: Maximum angle in degrees
    """
    print(f"Initializing servo on GPIO {gpio_pin}")
    print(f"Pulse width range: {min_pw}-{max_pw}ms")
    print(f"Angle range: {min_angle}-{max_angle} degrees")
    
    # Convert pulse width from milliseconds to seconds
    min_pw_sec = min_pw / 1000
    max_pw_sec = max_pw / 1000
    
    # Create servo object
    servo = AngularServo(
        pin=gpio_pin,
        min_pulse_width=min_pw_sec,
        max_pulse_width=max_pw_sec,
        min_angle=min_angle,
        max_angle=max_angle
    )
    
    try:
        # Test 1: Move to center position
        print("\nTest 1: Moving to center position...")
        center = (min_angle + max_angle) / 2
        servo.angle = center
        print(f"Servo set to {center} degrees")
        time.sleep(2)
        
        # Test 2: Move to minimum position
        print("\nTest 2: Moving to minimum position...")
        servo.angle = min_angle
        print(f"Servo set to {min_angle} degrees")
        time.sleep(2)
        
        # Test 3: Move to maximum position
        print("\nTest 3: Moving to maximum position...")
        servo.angle = max_angle
        print(f"Servo set to {max_angle} degrees")
        time.sleep(2)
        
        # Test 4: Sweep from min to max
        print("\nTest 4: Sweeping from min to max...")
        steps = 10
        step_size = (max_angle - min_angle) / steps
        
        for i in range(steps + 1):
            angle = min_angle + (i * step_size)
            servo.angle = angle
            print(f"Servo set to {angle:.1f} degrees")
            time.sleep(0.5)
        
        # Test 5: Interactive mode
        print("\nTest 5: Interactive mode")
        print("Enter angles between {} and {} degrees, or 'q' to quit".format(min_angle, max_angle))
        
        while True:
            user_input = input("Enter angle (or 'q' to quit): ")
            
            if user_input.lower() == 'q':
                break
            
            try:
                angle = float(user_input)
                if min_angle <= angle <= max_angle:
                    servo.angle = angle
                    print(f"Servo set to {angle} degrees")
                else:
                    print(f"Angle must be between {min_angle} and {max_angle} degrees")
            except ValueError:
                print("Invalid input. Please enter a number or 'q'")
        
    finally:
        # Center the servo and clean up
        print("\nCleaning up...")
        servo.angle = center
        time.sleep(1)
        servo.close()
        print("Servo test completed")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test a servo motor using gpiozero')
    parser.add_argument('--pin', type=int, default=17, help='GPIO pin number (BCM numbering)')
    parser.add_argument('--min-pw', type=float, default=0.5, help='Minimum pulse width in milliseconds')
    parser.add_argument('--max-pw', type=float, default=2.5, help='Maximum pulse width in milliseconds')
    parser.add_argument('--min-angle', type=float, default=0, help='Minimum angle in degrees')
    parser.add_argument('--max-angle', type=float, default=120, help='Maximum angle in degrees')
    
    args = parser.parse_args()
    
    # Run the servo test
    test_servo(
        gpio_pin=args.pin,
        min_pw=args.min_pw,
        max_pw=args.max_pw,
        min_angle=args.min_angle,
        max_angle=args.max_angle
    )
