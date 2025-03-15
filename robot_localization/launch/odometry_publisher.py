import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Float64  # If you want to send numeric data (like encoder position)

import serial
import time

class ArduinoSerialNode(Node):
    def __init__(self):
        super().__init__('arduino_serial_node')
        
        # Open serial connection to Arduino (change '/dev/ttyUSB0' to your device)
        self.serial_port = '/dev/ttyUSB0'  # or '/dev/ttyACM0' or your specific port
        self.baud_rate = 9600
        
        try:
            self.serial_connection = serial.Serial(self.serial_port, self.baud_rate)
            self.get_logger().info(f'Successfully connected to {self.serial_port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Error opening serial port: {e}')
            exit(1)
        
        # Create publishers for encoder position and motor status
        self.encoder_publisher = self.create_publisher(Float64, 'encoder_position', 10)
        self.motor_status_publisher = self.create_publisher(String, 'motor_status', 10)
        
        # Create a timer to check for new data from Arduino
        self.timer = self.create_timer(0.1, self.read_serial_data)  # Read every 100ms

    def read_serial_data(self):
        if self.serial_connection.in_waiting > 0:
            data = self.serial_connection.readline().decode('utf-8').strip()
            if data:
                # Parse the data sent by Arduino
                try:
                    position_str, motor_status = data.split(',')
                    position = float(position_str)  # Convert position to float

                    # Publish the encoder position
                    encoder_msg = Float64()
                    encoder_msg.data = position
                    self.encoder_publisher.publish(encoder_msg)
                    
                    # Publish the motor status
                    motor_status_msg = String()
                    motor_status_msg.data = motor_status
                    self.motor_status_publisher.publish(motor_status_msg)
                    
                    # Log the data
                    self.get_logger().info(f'Received encoder position: {position}, Motor status: {motor_status}')
                    
                except ValueError:
                    self.get_logger().error(f'Error parsing data: {data}')

def main(args=None):
    rclpy.init(args=args)

    arduino_serial_node = ArduinoSerialNode()

    try:
        rclpy.spin(arduino_serial_node)
    except KeyboardInterrupt:
        pass
    finally:
        arduino_serial_node.serial_connection.close()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
