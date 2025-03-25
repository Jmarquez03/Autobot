#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Point
from std_msgs.msg import Bool, String
import math
import time
import tf2_ros
from tf2_ros import TransformException

class MissionController(Node):
    def __init__(self):
        super().__init__('mission_controller')
        
        # Parameters
        self.declare_parameter('exploration_radius', 3.0)
        self.declare_parameter('exploration_points', 8)
        self.declare_parameter('fire_approach_distance', 0.5)
        self.declare_parameter('return_timeout', 180.0)  # seconds
        
        # Initialize state variables
        self.state = "INIT"
        self.start_pose = None
        self.current_pose = None
        self.fire_detected = False
        self.fire_location = None
        self.exploration_waypoints = []
        self.current_waypoint_index = 0
        self.mission_start_time = None
        self.navigation_active = False
        
        # Get parameters
        self.exploration_radius = self.get_parameter('exploration_radius').value
        self.exploration_points = self.get_parameter('exploration_points').value
        self.fire_approach_distance = self.get_parameter('fire_approach_distance').value
        self.return_timeout = self.get_parameter('return_timeout').value
        
        # Navigation action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # TF listener to get robot pose
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Subscribers
        self.fire_detection_sub = self.create_subscription(
            Bool, 
            '/fire_detection', 
            self.fire_detection_callback, 
            10)
            
        self.fire_location_sub = self.create_subscription(
            PoseStamped, 
            '/fire_location', 
            self.fire_location_callback, 
            10)
            
        # Publishers
        self.status_pub = self.create_publisher(
            String,
            '/mission_status',
            10)
            
        # self.hose_control_pub = self.create_publisher(
        #     String,
        #     '/hose_control',
        #     10)
            
        # Initialize timers
        self.state_timer = self.create_timer(1.0, self.state_machine_callback)
        self.pose_timer = self.create_timer(0.5, self.update_pose)
        self.status_timer = self.create_timer(0.5, self.publish_status)
        
        self.get_logger().info('Mission Controller initialized, waiting for navigation server...')
        self.nav_client.wait_for_server()  # Wait for the navigation server to be ready
        self.get_logger().info('Navigation server connected, ready to start mission')
        
    def update_pose(self):
        # Get current robot pose from TF
        try:
            trans = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time())
                
            # Create a pose
            current_pose = PoseStamped()
            current_pose.header.stamp = self.get_clock().now().to_msg()
            current_pose.header.frame_id = 'map'
            
            # Set position
            current_pose.pose.position.x = trans.transform.translation.x
            current_pose.pose.position.y = trans.transform.translation.y
            current_pose.pose.position.z = trans.transform.translation.z
            
            # Set orientation
            current_pose.pose.orientation.x = trans.transform.rotation.x
            current_pose.pose.orientation.y = trans.transform.rotation.y
            current_pose.pose.orientation.z = trans.transform.rotation.z
            current_pose.pose.orientation.w = trans.transform.rotation.w
            
            self.current_pose = current_pose
            
            # Store the starting position the first time we get a pose
            if self.start_pose is None:
                self.start_pose = current_pose
                self.get_logger().info(f'Initial pose set to: x={current_pose.pose.position.x}, y={current_pose.pose.position.y}')
                
        except TransformException as ex:
            self.get_logger().warning(f'Could not get robot pose: {ex}')
            
    def fire_detection_callback(self, msg):
        self.fire_detected = msg.data
        
    def fire_location_callback(self, msg):
        self.fire_location = msg
        self.get_logger().info(f'Received fire location: x={msg.pose.position.x}, y={msg.pose.position.y}')
        
    def send_navigation_goal(self, pose):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose
        
        self.get_logger().info(f'Navigating to: x={pose.pose.position.x}, y={pose.pose.position.y}')
        
        self.navigation_active = True
        send_goal_future = self.nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)
            
    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected by the navigation server')
            self.navigation_active = False
            self.current_waypoint_index += 1
            return
            
        self.get_logger().info('Goal accepted by the navigation server')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
        
    def get_result_callback(self, future):
        result = future.result().result
        status = future.result().status
        
        self.navigation_active = False
        
        if status == 4:  # Succeeded
            self.get_logger().info('Navigation goal reached successfully')
            self.current_waypoint_index += 1
        else:
            self.get_logger().error(f'Navigation goal failed with status {status}')
            # Try to continue with the next waypoint
            self.current_waypoint_index += 1
            
    def generate_exploration_waypoints(self):
        # Generate waypoints in a circular pattern for efficient exploration
        waypoints = []
        
        for i in range(self.exploration_points):
            angle = 2 * math.pi * i / self.exploration_points
            x = self.start_pose.pose.position.x + self.exploration_radius * math.cos(angle)
            y = self.start_pose.pose.position.y + self.exploration_radius * math.sin(angle)
            
            wp = PoseStamped()
            wp.header = self.start_pose.header
            wp.pose.position.x = x
            wp.pose.position.y = y
            
            # Set orientation to face the center for better sensing
            wp.pose.orientation.z = math.sin(-angle/2)
            wp.pose.orientation.w = math.cos(-angle/2)
            
            waypoints.append(wp)
            
        self.get_logger().info(f'Generated {len(waypoints)} exploration waypoints')
        return waypoints
        
    def distance_to_point(self, pose1, pose2):
        dx = pose1.pose.position.x - pose2.pose.position.x
        dy = pose1.pose.position.y - pose2.pose.position.y
        return math.sqrt(dx*dx + dy*dy)
        
    def state_machine_callback(self):
        if self.current_pose is None:
            self.get_logger().warn('No pose information available yet')
            return
            
        # State machine for autonomous mission
        if self.state == "INIT":
            self.get_logger().info('Initializing mission')
            
            # Record mission start time
            self.mission_start_time = self.get_clock().now()
            
            # Generate exploration waypoints
            self.exploration_waypoints = self.generate_exploration_waypoints()
            
            # Start exploration
            self.state = "EXPLORING"
            self.current_waypoint_index = 0
            
        elif self.state == "EXPLORING":
            # If fire detected, switch to approaching the fire
            if self.fire_detected and self.fire_location is not None:
                self.state = "APPROACHING_FIRE"
                self.get_logger().info('Fire detected, switching to approaching fire')
                
            # Continue with exploration waypoints
            elif self.current_waypoint_index < len(self.exploration_waypoints) and not self.navigation_active:
                self.send_navigation_goal(self.exploration_waypoints[self.current_waypoint_index])
            
            # If exploration complete but no fire found, do a second pass or return
            elif self.current_waypoint_index >= len(self.exploration_waypoints):
                # Check time constraints
                elapsed_time = (self.get_clock().now() - self.mission_start_time).nanoseconds / 1e9
                
                if elapsed_time > self.return_timeout:
                    self.state = "RETURNING"
                    self.get_logger().info('Time limit reached, returning to start without fire detection')
                else:
                    # Reset for another exploration pass
                    self.current_waypoint_index = 0
                    self.get_logger().info('First exploration pass complete, starting second pass')
            
        elif self.state == "APPROACHING_FIRE":
            # Send goal to move to the fire
            if not self.navigation_active:
                self.send_navigation_goal(self.fire_location)
                self.state = "AT_FIRE"
            
        elif self.state == "AT_FIRE":
            # Wait until navigation is done
            if not self.navigation_active:
                self.get_logger().info('Reached fire location, confirming position')
                # No need to wait, just record and return
                self.state = "RETURNING"
                self.get_logger().info('Fire location confirmed, returning to start')
            
        elif self.state == "RETURNING":
            # Return to the starting position
            if not self.navigation_active:
                self.send_navigation_goal(self.start_pose)
                self.state = "COMPLETED"
            
        elif self.state == "COMPLETED":
            # Wait until navigation is done
            if not self.navigation_active:
                self.get_logger().info('Mission completed! Robot returned to start position')
                
                # Calculate mission statistics
                elapsed_time = (self.get_clock().now() - self.mission_start_time).nanoseconds / 1e9
                
                stats = f"Mission Stats: Time={elapsed_time:.1f}s"
                if self.fire_detected:
                    stats += f", Fire found at x={self.fire_location.pose.position.x:.2f}, y={self.fire_location.pose.position.y:.2f}"
                else:
                    stats += ", No fire detected"
                    
                self.get_logger().info(stats)
                self.state = "IDLE"
                
        elif self.state == "IDLE":
            # Mission is complete, do nothing
            pass
    
    def publish_status(self):
        # Publish the current state for monitoring
        status_msg = String()
        status_msg.data = f"STATE: {self.state}"
        
        if self.fire_detected:
            status_msg.data += ", FIRE_DETECTED: YES"
        else:
            status_msg.data += ", FIRE_DETECTED: NO"
            
        if self.start_pose is not None and self.current_pose is not None:
            distance_to_start = self.distance_to_point(self.start_pose, self.current_pose)
            status_msg.data += f", DIST_TO_START: {distance_to_start:.2f}m"
            
        if self.mission_start_time is not None:
            elapsed_time = (self.get_clock().now() - self.mission_start_time).nanoseconds / 1e9
            status_msg.data += f", TIME: {elapsed_time:.1f}s"
            
        self.status_pub.publish(status_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MissionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
