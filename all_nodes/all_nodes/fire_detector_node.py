#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature, Float32
from std_msgs.msg import Float64
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
import math
import tf2_ros
from tf2_ros import TransformException

class FireDetectorNode(Node):
    def __init__(self):
        super().__init__('fire_detector_node')
        
        # Parameters
        self.declare_parameter('temperature_threshold', 50.0)
        self.declare_parameter('confidence_threshold', 0.7)
        self.declare_parameter('window_size', 10)
        
        # Thermocouple-specific parameters
        self.declare_parameter('thermocouple_topic', '/thermocouple/temperature')
        self.declare_parameter('thermocouple_message_type', 'float32')  # Options: temperature, float32, float64
        
        # Get parameters
        self.temp_threshold = self.get_parameter('temperature_threshold').value
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.window_size = self.get_parameter('window_size').value
        self.thermocouple_topic = self.get_parameter('thermocouple_topic').value
        self.msg_type = self.get_parameter('thermocouple_message_type').value
        
        # Set up subscribers based on thermocouple message type
        if self.msg_type == 'temperature':
            # Original Temperature message type
            self.temp_sub = self.create_subscription(
                Temperature,
                self.thermocouple_topic,
                self.temperature_callback,
                10)
                
        elif self.msg_type == 'float32':
            # Float32 message type (common for simple sensors)
            self.temp_sub = self.create_subscription(
                Float32,
                self.thermocouple_topic,
                self.float32_callback,
                10)
                
        elif self.msg_type == 'float64':
            # Float64 message type
            self.temp_sub = self.create_subscription(
                Float64,
                self.thermocouple_topic,
                self.float64_callback,
                10)
        
        self.get_logger().info(f'Thermocouple configured: Topic={self.thermocouple_topic}, Type={self.msg_type}')
            
        # Set up publishers
        self.fire_detected_pub = self.create_publisher(
            Bool,
            '/fire_detection',
            10)
            
        self.fire_location_pub = self.create_publisher(
            PoseStamped,
            '/fire_location',
            10)
            
        self.markers_pub = self.create_publisher(
            MarkerArray,
            '/fire_markers',
            10)
            
        # Initialize variables
        self.temp_window = []
        self.detection_history = []
        self.fire_detected = False
        self.fire_locations = []
        
        # Set up TF buffer/listener for getting robot pose
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Create timer for visualization
        self.marker_timer = self.create_timer(0.5, self.publish_markers)
        
        self.get_logger().info('Fire detector initialized with thermocouple support')
        
    def temperature_callback(self, msg):
        # Add temperature to window
        self.temp_window.append(msg.temperature)
        
        # Keep window at specified size
        if len(self.temp_window) > self.window_size:
            self.temp_window.pop(0)
            
        # Process temperature data for fire detection
        if len(self.temp_window) == self.window_size:
            self.process_temperature_data()
            
    def float32_callback(self, msg):
        # Add temperature to window
        self.temp_window.append(msg.data)
        
        # Keep window at specified size
        if len(self.temp_window) > self.window_size:
            self.temp_window.pop(0)
            
        # Process temperature data for fire detection
        if len(self.temp_window) == self.window_size:
            self.process_temperature_data()
            
    def float64_callback(self, msg):
        # Add temperature to window
        self.temp_window.append(msg.data)
        
        # Keep window at specified size
        if len(self.temp_window) > self.window_size:
            self.temp_window.pop(0)
            
        # Process temperature data for fire detection
        if len(self.temp_window) == self.window_size:
            self.process_temperature_data()
            
    def process_temperature_data(self):
        # Calculate statistics
        mean_temp = np.mean(self.temp_window)
        max_temp = np.max(self.temp_window)
        
        # Detect fire based on threshold
        fire_detected_now = max_temp > self.temp_threshold
        
        # Add to detection history
        self.detection_history.append(fire_detected_now)
        if len(self.detection_history) > self.window_size:
            self.detection_history.pop(0)
            
        # Calculate confidence
        if len(self.detection_history) > 0:
            confidence = sum(self.detection_history) / len(self.detection_history)
        else:
            confidence = 0.0
            
        # Determine final fire detection status
        if confidence >= self.confidence_threshold and not self.fire_detected:
            self.fire_detected = True
            self.record_fire_location()
            
            # Publish detection status
            msg = Bool()
            msg.data = True
            self.fire_detected_pub.publish(msg)
            
            self.get_logger().info(f'FIRE DETECTED! Temp={max_temp:.1f}°C, Confidence={confidence:.2f}')
            
        elif confidence < self.confidence_threshold and self.fire_detected:
            self.fire_detected = False
            
            # Publish updated status
            msg = Bool()
            msg.data = False
            self.fire_detected_pub.publish(msg)
            
            self.get_logger().info('Fire detection lost')
                    
    def record_fire_location(self):
        # Try to get the current robot position from TF
        try:
            trans = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time())
                
            # Create a fire location
            fire_loc = PoseStamped()
            fire_loc.header.stamp = self.get_clock().now().to_msg()
            fire_loc.header.frame_id = 'map'
            
            # Set position from transform
            fire_loc.pose.position.x = trans.transform.translation.x
            fire_loc.pose.position.y = trans.transform.translation.y
            fire_loc.pose.position.z = trans.transform.translation.z
            
            # Set orientation (identity)
            fire_loc.pose.orientation.w = 1.0
            
            # Add to known fire locations
            self.fire_locations.append(fire_loc)
            
            # Publish fire location
            self.fire_location_pub.publish(fire_loc)
            
            self.get_logger().info(f'Recorded fire location at x={fire_loc.pose.position.x:.2f}, y={fire_loc.pose.position.y:.2f}')
            
        except TransformException as ex:
            self.get_logger().error(f'Could not get robot position: {ex}')
            
    def publish_markers(self):
        # Create markers for fire locations
        marker_array = MarkerArray()
        
        for i, fire_loc in enumerate(self.fire_locations):
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = 'fire_locations'
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            
            # Set position
            marker.pose = fire_loc.pose
            
            # Set scale
            marker.scale.x = 0.3
            marker.scale.y = 0.3
            marker.scale.z = 0.3
            
            # Set color (red)
            marker.color.r = 1.0
            marker.color.g = 0.2
            marker.color.b = 0.0
            marker.color.a = 0.8
            
            marker_array.markers.append(marker)
            
        if marker_array.markers:
            self.markers_pub.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)
    node = FireDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
