import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped
from sensor_msgs.msg import JointState
import serial
import math

class TwistToAckermannConverter(Node):
    def __init__(self):
        super().__init__('twist_to_ackermann_converter')
        
        # Parameters
        self.declare_parameter('wheelbase', 0.3)  # Distance between front and rear axles
        self.declare_parameter('max_steering_angle', 0.6)  # ~35 degrees in radians
        self.declare_parameter('serial_port', '/dev/ttyUSB2')
        self.declare_parameter('baud_rate', 115200)
        
        self.wheelbase = self.get_parameter('wheelbase').value
        self.max_steering_angle = self.get_parameter('max_steering_angle').value
        
        # Setup serial connection to Arduino/ESP32
        try:
            self.serial_port = serial.Serial(
                self.get_parameter('serial_port').value,
                self.get_parameter('baud_rate').value,
                timeout=1.0
            )
            self.serial_available = True
            self.get_logger().info(f"Connected to {self.get_parameter('serial_port').value}")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            self.serial_available = False
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Publishers (for debugging)
        self.ackermann_pub = self.create_publisher(
            AckermannDriveStamped,
            'ackermann_cmd',
            10
        )
        
        # Add joint state publisher for steering visualization
        self.joint_state_pub = self.create_publisher(
            JointState,
            'steering_joint_states',
            10
        )
        
        # Current steering angle
        self.current_steering_angle = 0.0
        
        self.get_logger().info('Twist to Ackermann converter initialized')
    
    def cmd_vel_callback(self, msg):
        # Convert Twist to Ackermann steering commands
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z
        
        # Calculate steering angle using bicycle model
        if abs(linear_velocity) < 0.001:
            # Avoid division by zero
            steering_angle = 0.0
        else:
            # Ackermann steering formula
            steering_angle = math.atan2(angular_velocity * self.wheelbase, linear_velocity)
        
        # Limit steering angle
        steering_angle = max(min(steering_angle, self.max_steering_angle), -self.max_steering_angle)
        
        # Update current steering angle
        self.current_steering_angle = steering_angle
        
        # Create Ackermann message (for debugging/visualization)
        ackermann_msg = AckermannDriveStamped()
        ackermann_msg.header.stamp = self.get_clock().now().to_msg()
        ackermann_msg.header.frame_id = "base_footprint"
        ackermann_msg.drive.steering_angle = steering_angle
        ackermann_msg.drive.speed = linear_velocity
        
        self.ackermann_pub.publish(ackermann_msg)
        
        # Publish joint states for steering visualization
        self.publish_steering_joint_states(steering_angle)
        
        # Send command to ESP32
        if self.serial_available:
            try:
                # Format: "ACKERMANN:speed,steering_angle\n"
                command = f"ACKERMANN:{linear_velocity:.2f},{steering_angle:.2f}\n"
                self.serial_port.write(command.encode())
            except serial.SerialException as e:
                self.get_logger().error(f"Serial write error: {e}")
                self.serial_available = False
    
    def publish_steering_joint_states(self, steering_angle):
        # Create joint state message for steering joints
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        
        # Include only steering-related joints
        joint_state.name = [
            'steering_control_joint',
            'front_left_pivot_joint',
            'front_right_pivot_joint'
        ]
        
        # Set the same angle for all steering joints
        joint_state.position = [
            steering_angle,
            steering_angle,
            steering_angle
        ]
        
        # Publish the joint states
        self.joint_state_pub.publish(joint_state)

def main(args=None):
    rclpy.init(args=args)
    node = TwistToAckermannConverter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()