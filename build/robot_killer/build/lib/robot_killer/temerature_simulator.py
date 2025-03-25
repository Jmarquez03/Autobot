#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
import math

class TemperatureSimulator(Node):
    def __init__(self):
        super().__init__('temperature_simulator')
        
        # Parameters
        self.declare_parameter('base_temperature', 25.0)
        self.declare_parameter('hot_spot_x', 2.0)
        self.declare_parameter('hot_spot_y', 2.0)
        self.declare_parameter('hot_spot_radius', 0.5)
        self.declare_parameter('hot_spot_max_temp', 80.0)
        self.declare_parameter('publish_rate', 10.0)
        
        # Get parameters
        self.base_temp = self.get_parameter('base_temperature').value
        self.hot_spot_x = self.get_parameter('hot_spot_x').value
        self.hot_spot_y = self.get_parameter('hot_spot_y').value
        self.hot_spot_radius = self.get_parameter('hot_spot_radius').value
        self.hot_spot_max_temp = self.get_parameter('hot_spot_max_temp').value
        self.publish_rate = self.get_parameter('publish_rate').value
        
        # Publishers
        self.temp_pub = self.create_publisher(
            Temperature,
            '/thermal_sensor/temperature',
            10)
            
        # TF listener to get robot pose
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Timer
        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_temperature)
        
        self.get_logger().info('Temperature simulator initialized')
        
    def publish_temperature(self):
        # Try to get current robot position
        try:
            trans = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time())
                
            robot_x = trans.transform.translation.x
            robot_y = trans.transform.translation.y
            
            # Calculate distance to hot spot
            distance = math.sqrt((robot_x - self.hot_spot_x)**2 + (robot_y - self.hot_spot_y)**2)
            
            # Calculate temperature based on distance to hot spot
            if distance < self.hot_spot_radius:
                # Inside hot spot - maximum temperature
                temperature = self.hot_spot_max_temp
            else:
                # Temperature decreases with distance
                temperature = self.base_temp + max(0, self.hot_spot_max_temp - self.base_temp) * (
                    math.exp(-(distance - self.hot_spot_radius) / (self.hot_spot_radius * 2)))
                
            # Create temperature message
            temp_msg = Temperature()
            temp_msg.header.stamp = self.get_clock().now().to_msg()
            temp_msg.header.frame_id = 'base_link'
            temp_msg.temperature = temperature
            
            self.temp_pub.publish(temp_msg)
            
        except Exception as ex:
            # If we can't get pose, just publish ambient temperature
            temp_msg = Temperature()
            temp_msg.header.stamp = self.get_clock().now().to_msg()
            temp_msg.header.frame_id = 'base_link'
            temp_msg.temperature = self.base_temp
            
            self.temp_pub.publish(temp_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TemperatureSimulator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
