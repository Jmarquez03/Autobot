import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Quaternion
import math

class AutonomousNav(Node):
    def __init__(self):
        super().__init__('autonomous_nav')
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info("Autonomous navigation node ready")

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
        self.send_goal_future = self.nav_client.send_goal_async(goal_msg)
        self.get_logger().info(f"Sent goal to ({x}, {y}, {math.degrees(theta)}°)")

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