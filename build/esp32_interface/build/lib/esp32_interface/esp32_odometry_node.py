#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from tf2_ros import TransformBroadcaster
import serial
import json
import math
import time
from threading import Lock

class ESP32OdometryNode(Node):
    def __init__(self):
        super().__init__('esp32_odometry_node')
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('frame_id', 'odom')
        self.declare_parameter('child_frame_id', 'base_link')
        self.declare_parameter('publish_rate', 20.0)  # Hz
        
        # Get parameters
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        self.frame_id = self.get_parameter('frame_id').value
        self.child_frame_id = self.get_parameter('child_frame_id').value
        self.publish_rate = self.get_parameter('publish_rate').value
        
        # Initialize publishers
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        
        # Initialize TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Initialize subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)
            
        # Initialize serial communication
        try:
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=0.1
            )
            self.get_logger().info(f"Connected to ESP32 on {self.serial_port}")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to ESP32: {e}")
            self.serial_conn = None
        
        # Initialize odometry variables
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vth = 0.0
        self.last_time = self.get_clock().now()
        
        # Serial communication lock
        self.serial_lock = Lock()
        
        # Create timer for publishing odometry
        self.timer = self.create_timer(1.0 / self.publish_rate, self.update_odometry)
        
        self.get_logger().info('ESP32 Odometry Node initialized')
        
    def cmd_vel_callback(self, msg):
        """Send velocity commands to ESP32"""
        if self.serial_conn is None:
            self.get_logger().warning("Cannot send commands - no serial connection")
            return
            
        # Create command structure for ESP32
        command = {
            "linear_x": msg.linear.x,
            "linear_y": msg.linear.y,
            "angular_z": msg.angular.z
        }
        
        # Send command to ESP32
        try:
            with self.serial_lock:
                self.serial_conn.write((json.dumps(command) + '\n').encode())
        except Exception as e:
            self.get_logger().error(f"Failed to send command to ESP32: {e}")
    
    def read_from_esp32(self):
        """Read data from ESP32"""
        if self.serial_conn is None:
            return None
            
        try:
            with self.serial_lock:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    return line
        except Exception as e:
            self.get_logger().error(f"Error reading from ESP32: {e}")
            
        return None
    
    def update_odometry(self):
        """Read odometry from ESP32 and publish"""
        data = self.read_from_esp32()
        
        if data:
            try:
                # Try to parse the data as JSON
                odom_data = json.loads(data)
                
                # Check if we have the required fields
                if all(k in odom_data for k in ('x', 'y', 'theta', 'vx', 'vy', 'vth')):
                    # Update odometry values
                    self.x = float(odom_data['x'])
                    self.y = float(odom_data['y'])
                    self.theta = float(odom_data['theta'])
                    self.vx = float(odom_data['vx'])
                    self.vy = float(odom_data['vy'])
                    self.vth = float(odom_data['vth'])
                    
                    # Publish the odometry
                    self.publish_odometry()
            except json.JSONDecodeError:
                self.get_logger().warning(f"Received invalid JSON data: {data}")
            except ValueError as e:
                self.get_logger().warning(f"Error processing odometry data: {e}")
        
    def publish_odometry(self):
        """Publish odometry message and TF transform"""
        current_time = self.get_clock().now()
        
        # Create quaternion from yaw
        q = self.euler_to_quaternion(0.0, 0.0, self.theta)
        
        # Create and publish transform
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = self.frame_id
        t.child_frame_id = self.child_frame_id
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation = q
        
        self.tf_broadcaster.sendTransform(t)
        
        # Create and publish odometry
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id
        
        # Set position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q
        
        # Set velocity
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.linear.y = self.vy
        odom.twist.twist.linear.z = 0.0
        odom.twist.twist.angular.x = 0.0
        odom.twist.twist.angular.y = 0.0
        odom.twist.twist.angular.z = self.vth
        
        self.odom_pub.publish(odom)
        
    def euler_to_quaternion(self, roll, pitch, yaw):
        """Convert Euler angles to quaternion"""
        q = Quaternion()
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        q.w = cy * cp * cr + sy * sp * sr
        q.x = cy * cp * sr - sy * sp * cr
        q.y = sy * cp * sr + cy * sp * cr
        q.z = sy * cp * cr - cy * sp * sr
        
        return q

def main(args=None):
    rclpy.init(args=args)
    node = ESP32OdometryNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        if hasattr(node, 'serial_conn') and node.serial_conn is not None:
            node.serial_conn.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main() 