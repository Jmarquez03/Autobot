#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import serial
import time

class ThermocoupleNode(Node):
    def __init__(self):
        super().__init__('thermocouple_node')
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB3')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('publish_rate', 2.0)  # Hz
        
        # Get parameters
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        
        # Setup serial connection
        try:
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1.0
            )
            self.get_logger().info(f'Connected to Arduino on {self.serial_port} at {self.baud_rate} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port {self.serial_port}: {e}')
            raise
        
        # Create publisher
        self.temp_publisher = self.create_publisher(
            Float32,
            '/thermocouple/temperature',
            10)
            
        # Create timer for reading temperature
        self.timer = self.create_timer(1.0 / self.get_parameter('publish_rate').value, self.read_temperature)
        
    def read_temperature(self):
        try:
            # Check if data is available
            if self.serial.in_waiting > 0:
                # Read a line from serial
                line = self.serial.readline().decode('utf-8').strip()
                
                # Check if this is a temperature reading (starts with "C:")
                if line.startswith("C:"):
                    try:
                        # Extract the temperature value
                        temp_str = line[2:].strip()
                        temperature = float(temp_str)
                        
                        # Publish temperature
                        msg = Float32()
                        msg.data = temperature
                        self.temp_publisher.publish(msg)
                        
                        self.get_logger().debug(f'Published temperature: {temperature}°C')
                    except ValueError as e:
                        self.get_logger().warn(f'Failed to parse temperature value from "{line}": {e}')
                # If the line doesn't start with "C:", ignore it silently
                        
        except Exception as e:
            self.get_logger().error(f'Error reading temperature: {str(e)}')
            
    def destroy_node(self):
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
            self.get_logger().info('Closed serial connection')
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ThermocoupleNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()