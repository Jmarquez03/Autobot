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
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        
        # Get parameters
        self.serial_port_path = self.get_parameter('serial_port').get_parameter_value().string_value
        self.baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
        
        # Try to open serial port with error handling
        self.serial_available = False
        try:
            self.serial_port = serial.Serial(self.serial_port_path, self.baud_rate, timeout=1)
            self.serial_available = True
            self.get_logger().info(f"Connected to ESP32 on {self.serial_port_path}")
        except serial.SerialException as e:
            self.get_logger().error(f"Could not open serial port {self.serial_port_path}: {str(e)}")
            self.get_logger().warn("Running in simulation mode - odometry data will not be available")
            self.serial_port = None
        
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.timer = self.create_timer(0.01, self.update_odometry)  # 100Hz

    def cmd_vel_callback(self, msg):
        # Skip if serial is not available
        if not self.serial_available:
            return
            
        # Convert Twist to motor commands using differential drive kinematics
        wheel_separation = 0.2  # Must match ESP32 value
        left_speed = msg.linear.x - (msg.angular.z * wheel_separation / 2)
        right_speed = msg.linear.x + (msg.angular.z * wheel_separation / 2)
    
        # Send command in ESP32's expected format
        command = f"CMD:{left_speed:.2f},{right_speed:.2f}\n"  # NOTICE THE COLON
        try:
            self.serial_port.write(command.encode('ascii'))
        except serial.SerialException as e:
            self.get_logger().error(f"Serial write error: {str(e)}")
            self.serial_available = False  # Mark serial as unavailable after error


    def update_odometry(self):
        if not self.serial_available:
            return
            
        try:
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.readline().decode().strip().split(',')
                if len(data) == 6:
                    x, y, theta, vx, vy, vtheta = map(float, data)
                    
                    current_time = self.get_clock().now()
                    
                    # Create quaternion from yaw
                    odom_quat = Quaternion()
                    odom_quat.x = 0.0
                    odom_quat.y = 0.0
                    odom_quat.z = math.sin(theta / 2)
                    odom_quat.w = math.cos(theta / 2)

                    # Set up pose covariance (6x6)
                    pose_covariance = [
                        0.001, 0.0, 0.0, 0.0, 0.0, 0.0,      # x
                        0.0, 0.001, 0.0, 0.0, 0.0, 0.0,      # y
                        0.0, 0.0, 0.001, 0.0, 0.0, 0.0,      # z
                        0.0, 0.0, 0.0, 0.001, 0.0, 0.0,      # roll
                        0.0, 0.0, 0.0, 0.0, 0.001, 0.0,      # pitch
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.001       # yaw
                    ]

                    # Set up twist covariance (6x6)
                    twist_covariance = [
                        0.001, 0.0, 0.0, 0.0, 0.0, 0.0,      # vx
                        0.0, 0.001, 0.0, 0.0, 0.0, 0.0,      # vy
                        0.0, 0.0, 0.001, 0.0, 0.0, 0.0,      # vz
                        0.0, 0.0, 0.0, 0.001, 0.0, 0.0,      # angular vx
                        0.0, 0.0, 0.0, 0.0, 0.001, 0.0,      # angular vy
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.001       # angular vz
                    ]

                    # Create and fill odometry message
                    odom = Odometry()
                    odom.header.stamp = current_time.to_msg()
                    odom.header.frame_id = "odom"
                    odom.child_frame_id = "base_footprint"
                    
                    # Set pose
                    odom.pose.pose.position = Point(x=x, y=y, z=0.0)
                    odom.pose.pose.orientation = odom_quat
                    odom.pose.covariance = pose_covariance

                    # Set twist
                    odom.twist.twist.linear = Vector3(x=vx, y=vy, z=0.0)
                    odom.twist.twist.angular = Vector3(x=0.0, y=0.0, z=vtheta)
                    odom.twist.covariance = twist_covariance

                    self.odom_pub.publish(odom)

                    # Publish transform
                    t = TransformStamped()
                    t.header.stamp = current_time.to_msg()
                    t.header.frame_id = "odom"
                    t.child_frame_id = "base_footprint"
                    t.transform.translation.x = x
                    t.transform.translation.y = y
                    t.transform.translation.z = 0.0
                    t.transform.rotation = odom_quat

                    self.tf_broadcaster.sendTransform(t)
        except serial.SerialException as e:
            self.get_logger().error(f"Serial read error: {str(e)}")
            self.serial_available = False  # Mark as unavailable after error

def main(args=None):
    rclpy.init(args=args)
    node = ESP32OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
