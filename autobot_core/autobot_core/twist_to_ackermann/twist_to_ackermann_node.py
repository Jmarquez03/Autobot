import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped
import serial
import time

class TwistToAckermannConverter(Node):
    def __init__(self):
        super().__init__('twist_to_ackermann_converter')
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB2')
        self.serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        
        # Initialize serial connection
        try:
            # Add baud_rate parameter
            self.declare_parameter('baud_rate', 115200)
            self.baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
            
            # Use the parameter when initializing serial
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f'Connected to serial port: {self.serial_port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port {self.serial_port}: {str(e)}')
            self.ser = None
        
        # Create subscription to cmd_vel topic
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)
            
        # Create publisher for Ackermann drive commands
        self.publisher = self.create_publisher(
            AckermannDriveStamped,
            'ackermann_cmd',
            10)
            
        # Add visualization parameter
        self.declare_parameter('visualize', True)
        self.visualize = self.get_parameter('visualize').get_parameter_value().bool_value
        
        # Add visualization publisher if needed
        if self.visualize:
            self.marker_pub = self.create_publisher(
                Marker,
                'ackermann_marker',
                10)
        
        self.get_logger().info('Twist to Ackermann converter initialized')
        
        self.declare_parameter('min_angle', 45.0)    # Updated to 45°
        self.declare_parameter('max_angle', 135.0)  # Updated to 135°
        self.declare_parameter('neutral_angle', 90.0) # Center at 90°
        self.declare_parameter('max_angular', 1.0)   # Max turn rate in rad/s

    def cmd_vel_callback(self, msg):
        # Get parameters properly
        min_angle = self.get_parameter('min_angle').value
        max_angle = self.get_parameter('max_angle').value
        neutral_angle = self.get_parameter('neutral_angle').value
        max_angular = self.get_parameter('max_angular').value
        
        # Convert angular velocity to servo angle (45-135° range)
        steering_angle = neutral_angle + (msg.angular.z / max_angular) * (max_angle - neutral_angle)
        steering_angle = max(min(steering_angle, max_angle), min_angle)
        
        # Create SINGLE Ackermann message
        ackermann_msg = AckermannDriveStamped()
        ackermann_msg.header.stamp = self.get_clock().now().to_msg()
        ackermann_msg.header.frame_id = "base_footprint"
        ackermann_msg.drive.speed = msg.linear.x
        ackermann_msg.drive.steering_angle = steering_angle  # Use converted angle
        
        # Publish to ROS
        self.publisher.publish(ackermann_msg)
        
        # Send to serial ONCE with correct values
        if self.ser is not None:
            try:
                command = f"{msg.linear.x:.2f},{steering_angle:.2f}\n"
                self.ser.write(command.encode())
            except serial.SerialException as e:
                self.get_logger().error(f'Serial write error: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = TwistToAckermannConverter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
