#!/usr/bin/env python3

from math import sin, cos, pi
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Quaternion, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster, TransformStamped

class StatePublisher(Node):
    def __init__(self):
        super().__init__('state_publisher')
        
        # Set up QoS profile for reliable communication
        qos_profile = QoSProfile(depth=10)
        
        # Publishers and broadcasters
        self.joint_pub = self.create_publisher(JointState, 'joint_states', qos_profile)
        self.broadcaster = TransformBroadcaster(self, qos=qos_profile)
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)
            
        # Add odometry subscriber to receive data from ESP32
        self.odom_sub = self.create_subscription(
            Odometry,
            'odom',
            self.odom_callback,
            10)
        
        # Log node startup
        self.nodeName = self.get_name()
        self.get_logger().info("{0} started".format(self.nodeName))
        
        # Robot parameters
        self.wheel_radius = 0.05
        self.wheel_separation = 0.15
        
        # Motion state
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        
        # Joint state
        self.wheel_rotation = 0.0
        self.steering_angle = 0.0
        
        # Position state
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.theta = 0.0
        self.current_orientation = Quaternion()
        
        # Flag to track if we've received odometry data
        self.odom_received = False
        
        # Timer for state publishing (30Hz)
        self.timer = self.create_timer(0.033, self.timer_callback)

    def cmd_vel_callback(self, msg):
        """Process incoming velocity commands"""
        # Only use cmd_vel if we're not getting odometry data
        if not self.odom_received:
            self.linear_velocity = msg.linear.x
            self.angular_velocity = msg.angular.z
    
    def odom_callback(self, msg):
        """Process incoming odometry data from ESP32"""
        # Extract position
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.z = msg.pose.pose.position.z
        
        # Extract orientation
        self.current_orientation = msg.pose.pose.orientation
        
        # Extract velocities
        self.linear_velocity = msg.twist.twist.linear.x
        self.angular_velocity = msg.twist.twist.angular.z
        
        # Update steering angle based on angular velocity
        self.steering_angle = self.angular_velocity * 0.5  # Scale to reasonable range
        self.steering_angle = max(min(self.steering_angle, 0.5), -0.5)  # Limit range
        
        # Calculate wheel rotation from linear velocity
        wheel_rotation_rate = self.linear_velocity / self.wheel_radius
        self.wheel_rotation += wheel_rotation_rate * 0.033  # Assuming 30Hz
        self.wheel_rotation = self.wheel_rotation % (2 * pi)  # Keep within 0-2π
        
        # Mark that we've received odometry data
        self.odom_received = True

    def update_joint_states(self):
        """Update and publish joint states based on current motion"""
        now = self.get_clock().now()
        joint_state = JointState()
        joint_state.header.stamp = now.to_msg()
        
        # Set joint names to match URDF
        joint_state.name = [
            'steering_control_joint',
            'front_left_pivot_joint',
            'front_right_pivot_joint',
            'front_left_wheel_joint',
            'front_right_wheel_joint',
            'left_rear_wheel_joint',
            'right_rear_wheel_joint'
        ]
        
        # If not using odometry, calculate steering and rotation locally
        if not self.odom_received:
            # Integrate steering angle from angular velocity
            self.steering_angle += self.angular_velocity * 0.033
            self.steering_angle = max(min(self.steering_angle, 0.5), -0.5)
            
            # Integrate wheel rotation from linear velocity
            wheel_rotation_rate = self.linear_velocity / self.wheel_radius
            self.wheel_rotation += wheel_rotation_rate * 0.033
            self.wheel_rotation = self.wheel_rotation % (2 * pi)
        
        # Set joint positions
        joint_state.position = [
            self.steering_angle,          # steering_control_joint
            self.steering_angle,          # front_left_pivot_joint (mimics steering)
            self.steering_angle,          # front_right_pivot_joint (mimics steering)
            self.wheel_rotation,          # front_left_wheel_joint
            self.wheel_rotation,          # front_right_wheel_joint
            self.wheel_rotation,          # left_rear_wheel_joint
            self.wheel_rotation           # right_rear_wheel_joint
        ]
        
        return joint_state

    def update_transform(self):
        """Update transform between odom and base_footprint"""
        now = self.get_clock().now()
        odom_trans = TransformStamped()
        odom_trans.header.frame_id = 'odom'
        odom_trans.child_frame_id = 'base_footprint'
        odom_trans.header.stamp = now.to_msg()
        
        if not self.odom_received:
            # If no odometry data, calculate position locally
            dt = 0.033
            dx = self.linear_velocity * cos(self.theta) * dt
            dy = self.linear_velocity * sin(self.theta) * dt
            dtheta = self.angular_velocity * dt
            
            self.x += dx
            self.y += dy
            self.theta += dtheta
            
            # Use calculated orientation
            odom_trans.transform.rotation = self.euler_to_quaternion(0, 0, self.theta)
        else:
            # Use orientation from odometry
            odom_trans.transform.rotation = self.current_orientation
        
        # Always use the latest position
        odom_trans.transform.translation.x = self.x
        odom_trans.transform.translation.y = self.y
        odom_trans.transform.translation.z = self.z
        
        return odom_trans

    def euler_to_quaternion(self, roll, pitch, yaw):
        """Convert Euler angles to quaternion"""
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
        
    def timer_callback(self):
        """Regular timer callback to publish state updates"""
        # Update and publish joint states
        joint_state = self.update_joint_states()
        self.joint_pub.publish(joint_state)
        
        # Update and publish transform
        odom_trans = self.update_transform()
        self.broadcaster.sendTransform(odom_trans)

def main(args=None):
    rclpy.init(args=args)
    node = StatePublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
