#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped
import math

class TwistToAckermannConverter(Node):
    def __init__(self):
        super().__init__('twist_to_ackermann_converter')
        
        # Parameters
        self.declare_parameter('wheelbase', 0.19) #distance from front axle to rear axle (meters)
        self.declare_parameter('frame_id', 'base_footprint')
        self.declare_parameter('max_steering_angle', 1.57)  # ~90 degrees
        
        self.wheelbase = self.get_parameter('wheelbase').value
        self.frame_id = self.get_parameter('frame_id').value
        self.max_steering_angle = self.get_parameter('max_steering_angle').value
        
        # Create subscription to Twist messages
        self.twist_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.twist_callback,
            10
        )
        
        # Create publisher for AckermannDriveStamped messages
        self.ackermann_pub = self.create_publisher(
            AckermannDriveStamped,
            'ackermann_cmd',
            10
        )
        
        self.get_logger().info(
            f"Twist to Ackermann converter initialized.\n"
            f"Listening to /cmd_vel, publishing to /ackermann_cmd\n"
            f"Parameters: wheelbase={self.wheelbase}, frame_id={self.frame_id}"
        )
    
    def convert_trans_rot_vel_to_steering_angle(self, v, omega):
        """
        Convert linear and angular velocity to steering angle
        For Ackermann steering, the relationship is: tan(steering_angle) = (wheelbase * omega) / v
        """
        if abs(v) < 0.001:  # Avoid division by near-zero
            return 0.0
        
        # Calculate steering angle
        steering_angle = math.atan2(omega * self.wheelbase, v)
        
        # Limit steering angle to max value
        return max(-self.max_steering_angle, min(self.max_steering_angle, steering_angle))
    
    def twist_callback(self, twist_msg):
        """
        Callback function for Twist messages
        """
        # Create AckermannDriveStamped message
        ackermann_msg = AckermannDriveStamped()
        
        # Set header
        ackermann_msg.header.stamp = self.get_clock().now().to_msg()
        ackermann_msg.header.frame_id = self.frame_id
        
        # Convert twist to ackermann drive
        linear_velocity = twist_msg.linear.x
        angular_velocity = twist_msg.angular.z
        
        # Set steering angle
        ackermann_msg.drive.steering_angle = self.convert_trans_rot_vel_to_steering_angle(
            linear_velocity, angular_velocity
        )
        
        # Set speed
        ackermann_msg.drive.speed = linear_velocity
        
        # Publish the message
        self.ackermann_pub.publish(ackermann_msg)

def main(args=None):
    rclpy.init(args=args)
    converter = TwistToAckermannConverter()
    
    try:
        rclpy.spin(converter)
    except KeyboardInterrupt:
        pass
    finally:
        converter.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
