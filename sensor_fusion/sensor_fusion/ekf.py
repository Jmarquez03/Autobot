#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster, Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
import numpy as np

class SensorPublisherNode(Node):
    def __init__(self):
        super().__init__('sensor_publisher_node')
        
        # Create subscribers for IMU and odometry data
        self.imu_subscription = self.create_subscription(
            Imu,
            '/bno055/imu',
            self.imu_callback,
            10)
            
        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10)
        
        # Subscribe to the filtered odometry from the EKF
        self.filtered_odom_sub = self.create_subscription(
            Odometry,
            'odometry/filtered',  # This is what the EKF node publishes to before remapping
            self.filtered_odom_callback,
            10)
            
        # Create publisher for filtered odometry
        self.filtered_odom_publisher = self.create_publisher(
            Odometry,
            'odom/filtered',  # This matches your remapping in the launch file
            10)
            
        # TF broadcaster for publishing transforms
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Store latest sensor data
        self.latest_imu = None
        self.latest_odom = None
        self.latest_filtered_odom = None
        
        self.get_logger().info('Sensor publisher node initialized')
        
    def imu_callback(self, msg):
        self.latest_imu = msg
        self.get_logger().debug('Received IMU data')
        self.publish_fused_odometry()
        
    def odom_callback(self, msg):
        self.latest_odom = msg
        self.get_logger().debug('Received odometry data')
        self.publish_fused_odometry()
        
    def filtered_odom_callback(self, msg):
        self.latest_filtered_odom = msg
        self.get_logger().debug('Received filtered odometry data')
        
        # Forward the filtered odometry to our custom topic
        if self.latest_filtered_odom:
            self.filtered_odom_publisher.publish(self.latest_filtered_odom)
            
            # Also publish the transform if needed
            t = TransformStamped()
            t.header = self.latest_filtered_odom.header
            t.child_frame_id = self.latest_filtered_odom.child_frame_id
            t.transform.translation.x = self.latest_filtered_odom.pose.pose.position.x
            t.transform.translation.y = self.latest_filtered_odom.pose.pose.position.y
            t.transform.translation.z = 0.0
            t.transform.rotation = self.latest_filtered_odom.pose.pose.orientation
            
            # Publish the transform
            self.tf_broadcaster.sendTransform(t)
    
    def publish_fused_odometry(self):
        # This is just a placeholder - the actual fusion is done by the EKF
        # This method ensures we're publishing something even if the EKF isn't working
        if self.latest_odom and self.latest_imu and not self.latest_filtered_odom:
            fused_odom = Odometry()
            fused_odom.header.stamp = self.get_clock().now().to_msg()
            fused_odom.header.frame_id = 'odom'
            fused_odom.child_frame_id = 'base_footprint'
            
            # Use position from odometry
            fused_odom.pose.pose.position = self.latest_odom.pose.pose.position
            
            # Use orientation from IMU
            fused_odom.pose.pose.orientation = self.latest_imu.orientation
            
            # Set some reasonable covariance values
            fused_odom.pose.covariance = [0.1, 0.0, 0.0, 0.0, 0.0, 0.0,
                                         0.0, 0.1, 0.0, 0.0, 0.0, 0.0,
                                         0.0, 0.0, 0.1, 0.0, 0.0, 0.0,
                                         0.0, 0.0, 0.0, 0.1, 0.0, 0.0,
                                         0.0, 0.0, 0.0, 0.0, 0.1, 0.0,
                                         0.0, 0.0, 0.0, 0.0, 0.0, 0.1]
            
            # Publish the fused odometry
            self.filtered_odom_publisher.publish(fused_odom)

def main(args=None):
    rclpy.init(args=args)
    node = SensorPublisherNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
