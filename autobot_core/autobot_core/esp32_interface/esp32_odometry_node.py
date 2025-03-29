import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Quaternion, Point, Vector3
import serial
import math
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class ESP32OdometryNode(Node):
    def __init__(self):
        super().__init__('esp32_odometry_node')
        # Add frame ID parameters
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('base_frame_id', 'base_footprint')
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('publish_tf', True)
        
        # Initialize serial connection
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
        
        # Initialize transform broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Initialize odometry publisher
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        
        # Subscribe to cmd_vel from the Ackermann controller
        # Note: With ros2_control, we'll subscribe to the controller's output
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'ackermann_controller/cmd_vel',  # Updated topic name
            self.cmd_vel_callback,
            10
        )
        
        # Create timer for odometry updates
        self.timer = self.create_timer(0.02, self.update_odometry)  # 50Hz updates
        
        # Add synchronization in __init__
        if self.serial_available:
            self.serial_port.reset_input_buffer()
            self.serial_port.write(b"SYNC\n")
            self.get_logger().info("Serial buffer reset")

    def cmd_vel_callback(self, msg):
        """
        Callback for cmd_vel messages from the Ackermann controller
        Sends velocity commands to the ESP32
        """
        if not self.serial_available:
            return
            
        try:
            # Format command for ESP32: "VEL:linear_x,angular_z\n"
            # With Ackermann controller, these values represent the desired vehicle motion
            command = f"VEL:{msg.linear.x:.3f},{msg.angular.z:.3f}\n"
            self.serial_port.write(command.encode())
            self.get_logger().debug(f"Sent command: {command.strip()}")
        except Exception as e:
            self.get_logger().error(f"Error sending velocity command: {e}")

    def update_odometry(self):
        if not self.serial_available:
            return
            
        try:
            # Check if data is available
            if self.serial_port.in_waiting >= 20:  # Minimum expected data length
                raw_data = self.serial_port.readline().decode(errors='replace').strip()
                
                if not raw_data.startswith(("ERR:", "CMD:")) and ',' in raw_data:
                    data = raw_data.split(',')
                    if len(data) == 6:
                        x, y, theta, vx, vy, vtheta = map(float, data)
                        
                        # Debug output
                        self.get_logger().debug(f"Received odom: x={x}, y={y}, theta={theta}")
                        
                        current_time = self.get_clock().now()
                        
                        # Create quaternion from yaw
                        odom_quat = Quaternion()
                        odom_quat.x = 0.0
                        odom_quat.y = 0.0
                        odom_quat.z = math.sin(theta / 2)
                        odom_quat.w = math.cos(theta / 2)

                        # Set up pose covariance (6x6)
                        pose_covariance = [
                            0.01, 0.0, 0.0, 0.0, 0.0, 0.0,  # Tightened values
                            0.0, 0.01, 0.0, 0.0, 0.0, 0.0,
                            0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                            0.0, 0.0, 0.0, 0.05, 0.0, 0.0,
                            0.0, 0.0, 0.0, 0.0, 0.05, 0.0,
                            0.0, 0.0, 0.0, 0.0, 0.0, 0.1
                        ]
                        
                        twist_covariance = [
                            0.05, 0.0, 0.0, 0.0, 0.0, 0.0,
                            0.0, 0.05, 0.0, 0.0, 0.0, 0.0,
                            0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                            0.0, 0.0, 0.0, 0.1, 0.0, 0.0,
                            0.0, 0.0, 0.0, 0.0, 0.1, 0.0,
                            0.0, 0.0, 0.0, 0.0, 0.0, 0.2
                        ]

                        # Create and fill odometry message
                        odom = Odometry()
                        odom.header.stamp = current_time.to_msg()
                        odom.header.frame_id = self.get_parameter('odom_frame_id').value
                        odom.child_frame_id = self.get_parameter('base_frame_id').value
                        
                        # Set position
                        odom.pose.pose.position.x = x
                        odom.pose.pose.position.y = y
                        odom.pose.pose.position.z = 0.0
                        odom.pose.pose.orientation = odom_quat
                        odom.pose.covariance = pose_covariance
                        
                        # Set velocity
                        odom.twist.twist.linear.x = vx
                        odom.twist.twist.linear.y = vy
                        odom.twist.twist.linear.z = 0.0
                        odom.twist.twist.angular.x = 0.0
                        odom.twist.twist.angular.y = 0.0
                        odom.twist.twist.angular.z = vtheta
                        odom.twist.covariance = twist_covariance

                        # Publish odometry message
                        self.odom_pub.publish(odom)

                        # Publish transform if enabled
                        if self.get_parameter('publish_tf').value:
                            t = TransformStamped()
                            t.header.stamp = current_time.to_msg()
                            t.header.frame_id = self.get_parameter('odom_frame_id').value
                            t.child_frame_id = self.get_parameter('base_frame_id').value
                            
                            # Set transform translation
                            t.transform.translation.x = x
                            t.transform.translation.y = y
                            t.transform.translation.z = 0.0
                            
                            # Set transform rotation
                            t.transform.rotation = odom_quat
                            
                            # Send transform
                            self.tf_broadcaster.sendTransform(t)
                        
                    else:
                        self.get_logger().warn(f"Invalid data format: {raw_data}")
                
        except Exception as e:
            self.get_logger().error(f"Error processing odometry data: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ESP32OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
