#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time

# Don't initialize serial here - move it to inside the class
# ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
# time.sleep(2)  # Let that connection heat up

class ServoMaestro(Node):
    def __init__(self):
        super().__init__('servo_maestro')
        
        # Parameters
        self.declare_parameter('max_omega', 1.0)  # Radians/sec
        self.declare_parameter('serial_port', '/dev/ttyUSB1')  # Default serial port
        self.declare_parameter('baud_rate', 9600)  # Default baud rate
        
        # Get parameters
        self.max_omega = self.get_parameter('max_omega').value
        serial_port = self.get_parameter('serial_port').value
        baud_rate = self.get_parameter('baud_rate').value
        
        # Initialize serial connection
        self.get_logger().info(f"Opening serial port: {serial_port} at {baud_rate} baud")
        self.ser = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)  # Let that connection heat up
        
        self.twist_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.twist_callback,
            10
        )
        
        self.get_logger().info("Servo controller ready for action...")

    def _calculate_desired_angle(self, omega):
        """Convert angular velocity to servo positions"""
        center = 10  # Middle position
        min_angle = -30  # Lower bound
        max_angle = 50  # Upper bound
        
        # Calculate angle based on angular velocity
        angle = center + (omega / self.max_omega) * (max_angle - center)
        
        # Constrain angle to valid range
        return int(max(min_angle, min(max_angle, angle)))

    def _send_arduino_command(self, angle):
        """Send command to Arduino"""
        command = f"S{angle}\n"
        self.ser.write(command.encode())
        self.get_logger().info(f"Sent: {command.strip()}")
        
        # Read Arduino response
        response = self.ser.readline().decode().strip()
        if response:
            self.get_logger().info(f"Arduino response: {response}")

    def twist_callback(self, twist_msg):
        """Handle incoming twist commands"""
        angular_velocity = twist_msg.angular.z
        target_angle = self._calculate_desired_angle(angular_velocity)
        self._send_arduino_command(target_angle)

def main(args=None):
    rclpy.init(args=args)
    maestro = ServoMaestro()
    
    try:
        rclpy.spin(maestro)
    except KeyboardInterrupt:
        maestro.get_logger().info("Caught you blushing... shutting down gently")
    finally:
        maestro.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()
