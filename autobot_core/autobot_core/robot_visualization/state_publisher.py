#!/usr/bin/env python

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState

class StatePublisher(Node):
    def __init__(self):
        super().__init__('state_publisher')
        # This node now only logs cmd_vel for debugging purposes
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        
        # Match physical robot parameters for reference
        self.wheel_radius = 0.05  # Must match real wheels
        self.wheel_separation = 0.2  # Must match ESP32 node's wheel_separation
        
        # Node initialization
        self.get_logger().info(f"{self.get_name()} started - monitoring cmd_vel only")

    def cmd_vel_callback(self, msg):
        # Just log the received velocity commands for debugging
        self.get_logger().debug(f"Received cmd_vel: linear={msg.linear.x}, angular={msg.angular.z}")

def main():
    rclpy.init()
    node = StatePublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
