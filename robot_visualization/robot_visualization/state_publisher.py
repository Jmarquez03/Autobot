# #! /usr/bin/env python

from math import sin, cos, pi
import threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Quaternion
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster, TransformStamped

# class StatePublisher(Node):
#     def __init__(self):
#         super().__init__('state_publisher')

#         qos_profile = QoSProfile(depth=10)
#         self.joint_pub = self.create_publisher(JointState, 'joint_states', qos_profile)
#         self.broadcaster = TransformBroadcaster(self, qos=qos_profile)
        
#         self.nodeName = self.get_name()
#         self.get_logger().info("{0} started".format(self.nodeName))

#         degree = pi / 180.0
#         loop_rate = self.create_rate(30)

#         # robot state
#         steering_angle = 0.0
#         steering_inc = degree * 2  # Increment for steering
#         wheel_rotation = 0.0
#         wheel_inc = degree * 5     # Wheel rotation speed

#         # message declarations
#         odom_trans = TransformStamped()
#         odom_trans.header.frame_id = 'odom'
#         odom_trans.child_frame_id = 'base_footprint'

#         joint_state = JointState()

#         try:
#             while rclpy.ok():
#                 rclpy.spin_once(self)

#                 # update joint_state
#                 now = self.get_clock().now()
#                 joint_state.header.stamp = now.to_msg()
                
#                 # Update joint names to match your URDF
#                 joint_state.name = [
#                     'steering_control_joint',
#                     'front_left_pivot_joint',
#                     'front_right_pivot_joint',
#                     'front_left_wheel_joint',
#                     'front_right_wheel_joint',
#                     'left_rear_wheel_joint',
#                     'right_rear_wheel_joint'
#                 ]
                
#                 # Update joint positions
#                 # Steering joints follow the steering angle
#                 # Wheel joints rotate continuously
#                 joint_state.position = [
#                     steering_angle,                # steering_control_joint
#                     steering_angle,                # front_left_pivot_joint (mimics steering)
#                     steering_angle,                # front_right_pivot_joint (mimics steering)
#                     wheel_rotation,                # front_left_wheel_joint
#                     wheel_rotation,                # front_right_wheel_joint
#                     wheel_rotation,                # left_rear_wheel_joint
#                     wheel_rotation                 # right_rear_wheel_joint
#                 ]

#                 # update transform
#                 odom_trans.header.stamp = now.to_msg()
                
#                 # Make the robot move in a circle
#                 radius = 1.0
#                 robot_angle = wheel_rotation / 10.0  # Slower movement
                
#                 odom_trans.transform.translation.x = cos(robot_angle) * radius
#                 odom_trans.transform.translation.y = sin(robot_angle) * radius
#                 odom_trans.transform.translation.z = 0.0
                
#                 # Set the robot's orientation to face the direction of travel
#                 odom_trans.transform.rotation = euler_to_quaternion(0, 0, robot_angle + pi/2)

#                 # send the joint state and transform
#                 self.joint_pub.publish(joint_state)
#                 self.broadcaster.sendTransform(odom_trans)

#                 # Create new robot state
#                 steering_angle += steering_inc
                
#                 # Oscillate the steering between limits
#                 if abs(steering_angle) > 0.4:  # Stay within the limits defined in URDF
#                     steering_inc *= -1
                
#                 # Continuously rotate the wheels
#                 wheel_rotation += wheel_inc
                
#                 # Keep wheel_rotation within reasonable bounds
#                 if wheel_rotation > 2*pi:
#                     wheel_rotation -= 2*pi

#                 # This will adjust as needed per iteration
#                 loop_rate.sleep()

#         except KeyboardInterrupt:
#             pass

# def euler_to_quaternion(roll, pitch, yaw):
#     qx = sin(roll/2) * cos(pitch/2) * cos(yaw/2) - cos(roll/2) * sin(pitch/2) * sin(yaw/2)
#     qy = cos(roll/2) * sin(pitch/2) * cos(yaw/2) + sin(roll/2) * cos(pitch/2) * sin(yaw/2)
#     qz = cos(roll/2) * cos(pitch/2) * sin(yaw/2) - sin(roll/2) * sin(pitch/2) * cos(yaw/2)
#     qw = cos(roll/2) * cos(pitch/2) * cos(yaw/2) + sin(roll/2) * sin(pitch/2) * sin(yaw/2)
    
#     return Quaternion(x=qx, y=qy, z=qz, w=qw)

# def main():
#     rclpy.init()
#     node = StatePublisher()

# if __name__ == '__main__':
#     main()
#! /usr/bin/env python

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
        
        qos_profile = QoSProfile(depth=10)
        self.joint_pub = self.create_publisher(JointState, 'joint_states', qos_profile)
        self.broadcaster = TransformBroadcaster(self, qos=qos_profile)
        
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)
        
        self.nodeName = self.get_name()
        self.get_logger().info("{0} started".format(self.nodeName))
        
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.wheel_radius = 0.05
        self.wheel_separation = 0.15
        
        self.wheel_rotation = 0.0
        self.steering_angle = 0.0
        
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

    def cmd_vel_callback(self, msg):
        self.linear_velocity = msg.linear.x
        self.angular_velocity = msg.angular.z

    def update_joint_states(self):
        now = self.get_clock().now()
        joint_state = JointState()
        joint_state.header.stamp = now.to_msg()
        joint_state.name = [
            'steering_control_joint',
            'front_left_pivot_joint',
            'front_right_pivot_joint',
            'front_left_wheel_joint',
            'front_right_wheel_joint',
            'left_rear_wheel_joint',
            'right_rear_wheel_joint'
        ]
        
        self.steering_angle += self.angular_velocity * 0.033
        self.steering_angle = max(min(self.steering_angle, 0.5), -0.5)
        
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
        now = self.get_clock().now()
        odom_trans = TransformStamped()
        odom_trans.header.frame_id = 'odom'
        odom_trans.child_frame_id = 'base_footprint'
        odom_trans.header.stamp = now.to_msg()
        
        dt = 0.033
        dx = self.linear_velocity * cos(self.steering_angle) * dt
        dy = self.linear_velocity * sin(self.steering_angle) * dt
        dtheta = self.angular_velocity * dt
        
        self.x += dx
        self.y += dy
        self.theta += dtheta
        
        odom_trans.transform.translation.x = self.x
        odom_trans.transform.translation.y = self.y
        odom_trans.transform.translation.z = 0.0
        odom_trans.transform.rotation = self.euler_to_quaternion(0, 0, self.theta)
        
        return odom_trans

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

    def run(self):
        try:
            while rclpy.ok():
                rclpy.spin_once(self)
                
                joint_state = self.update_joint_states()
                odom_trans = self.update_transform()
                
                self.joint_pub.publish(joint_state)
                self.broadcaster.sendTransform(odom_trans)
                
                self.get_clock().sleep_for(rclpy.duration.Duration(seconds=0.033))
                
        except KeyboardInterrupt:
            pass

def main():
    rclpy.init()
    node = StatePublisher()
    node.run()

if __name__ == '__main__':
    main()
