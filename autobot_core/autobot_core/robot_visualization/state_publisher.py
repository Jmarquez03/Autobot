#!/usr/bin/env python

from math import sin, cos, pi
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Quaternion, Twist
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster, TransformStamped

class StatePublisher(Node):
    def __init__(self):
        super().__init__('state_publisher')
        
        # Publishers and Subscribers
        qos_profile = QoSProfile(depth=10)
        self.joint_pub = self.create_publisher(JointState, 'joint_states', qos_profile)
        self.broadcaster = TransformBroadcaster(self, qos=qos_profile)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        
        # Robot parameters
        self.wheel_radius = 0.05
        self.wheel_separation = 0.15
        
        # State variables
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.wheel_rotation = 0.0
        self.steering_angle = 0.0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # Node initialization
        self.get_logger().info(f"{self.get_name()} started")

    def cmd_vel_callback(self, msg):
        self.linear_velocity = msg.linear.x
        self.angular_velocity = msg.angular.z

    def update_joint_states(self):
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        joint_state.name = [
            'steering_control_joint',
            'front_left_pivot_joint',
            'front_right_pivot_joint',
            'front_left_wheel_joint',
            'front_right_wheel_joint',
            'left_rear_wheel_joint',
            'right_rear_wheel_joint'
        ]
        
        # Update steering angle based on angular velocity
        self.steering_angle += self.angular_velocity * 0.033
        self.steering_angle = max(min(self.steering_angle, 0.5), -0.5)
        
        # Update wheel rotation based on linear velocity
        wheel_rotation_rate = self.linear_velocity / self.wheel_radius
        self.wheel_rotation += wheel_rotation_rate * 0.033
        self.wheel_rotation = self.wheel_rotation % (2 * pi)
        
        joint_state.position = [
            self.steering_angle,
            self.steering_angle,
            self.steering_angle,
            self.wheel_rotation,
            self.wheel_rotation,
            self.wheel_rotation,
            self.wheel_rotation
        ]
        
        return joint_state

    def update_transform(self):
        # COMPLETELY REMOVE THIS METHOD
        pass

    def run(self):
        try:
            while rclpy.ok():
                rclpy.spin_once(self)
                
                joint_state = self.update_joint_states()
                
                # Only publish joint states, not transforms
                self.joint_pub.publish(joint_state)
                
                self.get_clock().sleep_for(rclpy.duration.Duration(seconds=0.033))
                
        except KeyboardInterrupt:
            pass

    def euler_to_quaternion(self, roll, pitch, yaw):
        cy = cos(yaw * 0.5)
        sy = sin(yaw * 0.5)
        cp = cos(pitch * 0.5)
        sp = sin(pitch * 0.5)
        cr = cos(roll * 0.5)
        sr = sin(roll * 0.5)

        qw = cy * cp * cr + sy * sp * sr
        qx = cy * cp * sr - sy * sp * cr
        qy = sy * cp * sr + cy * sp * cr
        qz = sy * cp * cr - cy * sp * sr

        return Quaternion(x=qx, y=qy, z=qz, w=qw)

def main():
    rclpy.init()
    node = StatePublisher()
    node.run()

if __name__ == '__main__':
    main()
