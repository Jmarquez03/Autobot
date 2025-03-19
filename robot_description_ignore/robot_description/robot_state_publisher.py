import rclpy
from rclpy.node import Node
import os
from ament_index_python.packages import get_package_share_directory
import xacro
from robot_state_publisher import RobotStatePublisher
from sensor_msgs.msg import JointState
from std_msgs.msg import String

class URDFPublisherNode(Node):
    def __init__(self):
        super().__init__('urdf_publisher_node')
        
        # Declare parameters
        self.declare_parameter('robot_description_file', 'urdf/robot.urdf')
        self.declare_parameter('publish_rate', 50.0)
        
        # Get parameters
        robot_description_file = self.get_parameter('robot_description_file').value
        publish_rate = self.get_parameter('publish_rate').value
        
        # Get the path to the URDF file
        pkg_dir = get_package_share_directory('robot_description')
        urdf_file = os.path.join(pkg_dir, 'urdf/robot.urdf')
        
        # Load and process the URDF file
        with open(urdf_file, 'r') as file:
            robot_description = file.read()
        
        # Create a publisher for the robot description
        self.robot_description_publisher = self.create_publisher(
            String, 
            'robot_description', 
            10
        )
        
        # Publish the robot description
        msg = String()
        msg.data = robot_description
        self.robot_description_publisher.publish(msg)
        
        # Create a publisher for joint states
        self.joint_state_publisher = self.create_publisher(
            JointState,
            'joint_states',
            10
        )
        
        # Create a timer for publishing joint states
        self.timer = self.create_timer(1.0/publish_rate, self.publish_joint_states)
        
        self.get_logger().info('URDF Publisher Node started')
    
    def publish_joint_states(self):
        # Create a joint state message
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        
        # Add your robot's joint names and positions here
        # For example:
        joint_state.name = ['steering_joint', 'front_left_wheel_joint', 'front_right_wheel_joint', 
                           'left_rear_wheel_joint', 'right_rear_wheel_joint']
        joint_state.position = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        # Publish the joint state
        self.joint_state_publisher.publish(joint_state)

def main(args=None):
    rclpy.init(args=args)
    urdf_publisher_node = URDFPublisherNode()
    try:
        rclpy.spin(urdf_publisher_node)
    except KeyboardInterrupt:
        pass
    finally:
        urdf_publisher_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
