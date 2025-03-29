#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
import math

class JointStatePublisherNode(Node):
    def __init__(self):
        super().__init__('joint_state_publisher')
        
        # Create a publisher for the combined joint states
        self.joint_state_pub = self.create_publisher(
            JointState,
            'joint_states',
            10
        )
        
        # Subscribe to the steering joint states from twist_to_ackermann
        self.steering_sub = self.create_subscription(
            JointState,
            'steering_joint_states',
            self.steering_callback,
            10
        )
        
        # Subscribe to cmd_vel to calculate wheel rotations
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Store the latest steering joint states
        self.latest_steering = None
        
        # Parameters for wheel rotation calculation
        self.wheel_radius = 0.05  # Must match URDF
        self.wheel_rotation = 0.0
        self.linear_velocity = 0.0
        
        # Create a timer for wheel rotation updates
        self.timer = self.create_timer(0.033, self.update_wheel_rotation)
        
        self.get_logger().info('Joint state publisher initialized')
    
    def steering_callback(self, msg):
        # Update the latest steering joint states
        self.latest_steering = msg
        
        # Publish combined joint states
        self.publish_combined_joint_states()
    
    def cmd_vel_callback(self, msg):
        # Update linear velocity for wheel rotation calculation
        self.linear_velocity = msg.linear.x
    
    def update_wheel_rotation(self):
        # Update wheel rotation based on linear velocity
        wheel_rotation_rate = self.linear_velocity / self.wheel_radius
        self.wheel_rotation += wheel_rotation_rate * 0.033
        self.wheel_rotation = self.wheel_rotation % (2 * math.pi)
        
        # Publish combined joint states
        self.publish_combined_joint_states()
    
    def publish_combined_joint_states(self):
        # Create combined joint state message
        combined_msg = JointState()
        combined_msg.header.stamp = self.get_clock().now().to_msg()
        
        # Initialize with wheel joints
        combined_msg.name = [
            'left_rear_wheel_joint',
            'right_rear_wheel_joint',
            'front_left_wheel_joint',
            'front_right_wheel_joint'
        ]
        
        combined_msg.position = [
            self.wheel_rotation,
            self.wheel_rotation,
            self.wheel_rotation,
            self.wheel_rotation
        ]
        
        # Add steering joints if available
        if self.latest_steering is not None:
            combined_msg.name.extend(self.latest_steering.name)
            combined_msg.position.extend(self.latest_steering.position)
        
        # Publish the combined joint states
        self.joint_state_pub.publish(combined_msg)

def main(args=None):
    rclpy.init(args=args)
    node = JointStatePublisherNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()