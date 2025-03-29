import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive
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
        self.declare_parameter('use_ros2_control', True)
        
        self.wheelbase = self.get_parameter('wheelbase').value
        self.max_steering_angle = self.get_parameter('max_steering_angle').value
        self.use_ros2_control = self.get_parameter('use_ros2_control').value
        
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
        if self.use_ros2_control:
            # When using ros2_control, subscribe to the controller's output
            self.cmd_vel_sub = self.create_subscription(
                Twist,
                'ackermann_controller/cmd_vel',
                self.cmd_vel_callback,
                10
            )
        else:
            # Traditional subscription to cmd_vel
            self.cmd_vel_sub = self.create_subscription(
                Twist,
                'cmd_vel',
                self.cmd_vel_callback,
                10
            )
        
        # Publishers (for debugging)
        self.ackermann_pub = self.create_publisher(
            AckermannDrive,
            'ackermann_drive',  # For debugging/visualization
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
        
        self.get_logger().info(f'Twist to Ackermann converter initialized (ros2_control: {self.use_ros2_control})')
    
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
        ackermann_msg = AckermannDrive()
        ackermann_msg.steering_angle = steering_angle
        ackermann_msg.speed = linear_velocity
        
        self.ackermann_pub.publish(ackermann_msg)
        
        # Publish joint states for steering visualization
        self.publish_steering_joint_states(steering_angle)
        
        # Send command to ESP32 if not using ros2_control
        if self.serial_available and not self.use_ros2_control:
            try:
                # Format: "ACKERMANN:speed,steering_angle\n"
                command = f"ACKERMANN:{linear_velocity:.4f},{steering_angle:.4f}\n"
                self.serial_port.write(command.encode())
            except serial.SerialException as e:
                self.get_logger().error(f"Error sending command: {e}")
    
    def publish_steering_joint_states(self, steering_angle):
        # Create joint state message for steering visualization
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        
        # Set joint names and positions
        joint_state.name = ['front_left_pivot_joint', 'front_right_pivot_joint']
        joint_state.position = [steering_angle, steering_angle]
        
        # Publish joint states
        self.joint_state_pub.publish(joint_state)

def main(args=None):
    rclpy.init(args=args)
    node = TwistToAckermannConverter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()