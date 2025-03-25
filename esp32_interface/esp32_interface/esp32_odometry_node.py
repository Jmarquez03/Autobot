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
        self.serial_port = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.timer = self.create_timer(0.01, self.update_odometry)  # 100Hz

    def cmd_vel_callback(self, msg):
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


    def update_odometry(self):
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

                # Publish odometry message
                odom = Odometry()
                odom.header.stamp = current_time.to_msg()
                odom.header.frame_id = "odom"
                odom.child_frame_id = "base_footprint"
                
                odom.pose.pose.position = Point(x=x, y=y, z=0.0)
                odom.pose.pose.orientation = odom_quat
                odom.twist.twist.linear = Vector3(x=vx, y=vy, z=0.0)
                odom.twist.twist.angular = Vector3(x=0.0, y=0.0, z=vtheta)

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

def main(args=None):
    rclpy.init(args=args)
    node = ESP32OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
