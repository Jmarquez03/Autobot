import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Quaternion, Twist
import math
import time

class AutonomousNav(Node):
    def __init__(self):
        super().__init__('autonomous_nav')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Add a publisher for direct velocity control
        self.cmd_vel_pub = self.create_publisher(
            Twist, 
            'ackermann_controller/cmd_vel',  # Updated to use Ackermann controller topic
            10
        )
        
        # Parameters for navigation
        self.declare_parameter('use_ackermann', True)
        self.declare_parameter('max_linear_speed', 0.5)  # m/s
        self.declare_parameter('max_angular_speed', 0.8)  # rad/s
        
        self.get_logger().info("Autonomous navigation node ready")
        self.goal_handle = None

    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        
        q = Quaternion()
        q.z = math.sin(theta/2)
        q.w = math.cos(theta/2)
        goal_msg.pose.pose.orientation = q
        
        self.nav_client.wait_for_server()
        
        # Send the goal and add callbacks
        self.send_goal_future = self.nav_client.send_goal_async(
            goal_msg, 
            feedback_callback=self.feedback_callback
        )
        self.send_goal_future.add_done_callback(self.goal_response_callback)
        
        self.get_logger().info(f"Sent goal to ({x}, {y}, {math.degrees(theta)}°)")

    def goal_response_callback(self, future):
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().error('Goal was rejected!')
            return
            
        self.get_logger().info('Goal accepted!')
        self.goal_handle = goal_handle
        
        # Get the result
        self.result_future = goal_handle.get_result_async()
        self.result_future.add_done_callback(self.get_result_callback)
    
    def get_result_callback(self, future):
        result = future.result().result
        status = future.result().status
        
        if status == 4:
            self.get_logger().info('Goal succeeded!')
            # Send a stop command to ensure the robot stops
            self.stop_robot()
        else:
            self.get_logger().error(f'Goal failed with status: {status}')
            # Also stop the robot on failure
            self.stop_robot()
    
    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        # Extract current pose from feedback
        current_x = feedback.current_pose.pose.position.x
        current_y = feedback.current_pose.pose.position.y
        
        # Log progress occasionally (not every feedback to avoid spam)
        if hasattr(self, 'last_feedback_time'):
            current_time = self.get_clock().now()
            if (current_time - self.last_feedback_time).nanoseconds > 1e9:  # 1 second
                self.get_logger().info(f'Current position: ({current_x:.2f}, {current_y:.2f})')
                self.last_feedback_time = current_time
        else:
            self.last_feedback_time = self.get_clock().now()
    
    def stop_robot(self):
        """Send a zero velocity command to stop the robot"""
        stop_cmd = Twist()
        stop_cmd.linear.x = 0.0
        stop_cmd.angular.z = 0.0
        
        # Publish the stop command multiple times to ensure it's received
        for _ in range(3):
            self.cmd_vel_pub.publish(stop_cmd)
            time.sleep(0.1)

def main(args=None):
    rclpy.init(args=args)
    nav_node = AutonomousNav()
    
    # Example goal - replace with your coordinates
    nav_node.send_goal(2.0, 1.5, math.radians(45))
    
    rclpy.spin(nav_node)
    nav_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()