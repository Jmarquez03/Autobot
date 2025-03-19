# import rclpy
# from rclpy.node import Node
# from std_msgs.msg import String, Float64
# from nav_msgs.msg import Odometry
# from geometry_msgs.msg import Quaternion, TransformStamped
# from tf2_ros import TransformBroadcaster
# import serial
# import time
# import math
# from transforms3d.euler import euler2quat  # For ROS2/tf2

# class ArduinoSerialNode(Node):
#     def __init__(self):
#         super().__init__('arduino_serial_node')
        
#         # Open serial connection to Arduino
#         self.serial_port = '/dev/ttyUSB1'  # or '/dev/ttyACM0' or your specific port
#         self.baud_rate = 9600
        
#         try:
#             self.serial_connection = serial.Serial(self.serial_port, self.baud_rate)
#             self.get_logger().info(f'Successfully connected to {self.serial_port}')
#         except serial.SerialException as e:
#             self.get_logger().error(f'Error opening serial port: {e}')
#             exit(1)
        
#         # Create tf2 broadcaster
#         self.tf_broadcaster = TransformBroadcaster(self)
        
#         # Create odometry publisher for SLAM toolbox
#         self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        
#         # Keep original publishers
#         self.encoder_publisher = self.create_publisher(Float64, 'encoder_position', 10)
#         self.motor_status_publisher = self.create_publisher(String, 'motor_status', 10)
        
#         # Create a timer to check for new data from Arduino
#         self.timer = self.create_timer(0.1, self.read_serial_data)  # Read every 100ms
        
#         # Initialize odometry values
#         self.x = 0.0
#         self.y = 0.0
#         self.theta = 0.0
#         self.vx = 0.0
#         self.vy = 0.0
#         self.vtheta = 0.0

#     def read_serial_data(self):
#         if self.serial_connection.in_waiting > 0:
#             data = self.serial_connection.readline().decode('utf-8').strip()
#             if data:
#                 try:
#                     # Check if we have odometry data (x,y,theta,vx,vy,vtheta)
#                     values = data.split(',')
#                     if len(values) >= 6:
#                         self.x = float(values[0])
#                         self.y = float(values[1])
#                         self.theta = float(values[2])
#                         self.vx = float(values[3])
#                         self.vy = float(values[4])
#                         self.vtheta = float(values[5])
                        
#                         # Publish odometry data
#                         self.publish_odometry()
                        
#                         self.get_logger().info(f'Published odometry: x={self.x}, y={self.y}, theta={self.theta}')
                    
#                     # If we have the original format (position,status)
#                     elif len(values) == 2:
#                         position_str, motor_status = values
#                         position = float(position_str)  # Convert position to float

#                         # Publish the encoder position
#                         encoder_msg = Float64()
#                         encoder_msg.data = position
#                         self.encoder_publisher.publish(encoder_msg)
                        
#                         # Publish the motor status
#                         motor_status_msg = String()
#                         motor_status_msg.data = motor_status
#                         self.motor_status_publisher.publish(motor_status_msg)
                        
#                         # Log the data
#                         self.get_logger().info(f'Received encoder position: {position}, Motor status: {motor_status}')
                
#                 except ValueError as e:
#                     self.get_logger().error(f'Error parsing data: {data}, error: {e}')
    
#     def publish_odometry(self):
#         # Create and publish odometry message
#         odom_msg = Odometry()
#         now = self.get_clock().now()
#         odom_msg.header.stamp = now.to_msg()
#         odom_msg.header.frame_id = 'odom'
#         odom_msg.child_frame_id = 'base_link'
        
#         # Set position
#         odom_msg.pose.pose.position.x = self.x
#         odom_msg.pose.pose.position.y = self.y
#         odom_msg.pose.pose.position.z = 0.0
        
#         # Set orientation (convert theta to quaternion)
#         qx, qy, qz, qw = euler2quat(0, 0, self.theta)
#         odom_msg.pose.pose.orientation = Quaternion(x=qx, y=qy, z=qz, w=qw)
        
#         # Set velocity
#         odom_msg.twist.twist.linear.x = self.vx
#         odom_msg.twist.twist.linear.y = self.vy
#         odom_msg.twist.twist.angular.z = self.vtheta
        
#         # Publish odometry message
#         self.odom_publisher.publish(odom_msg)
        
#         # Broadcast transform using tf2
#         transform = TransformStamped()
#         transform.header.stamp = now.to_msg()
#         transform.header.frame_id = 'odom'
#         transform.child_frame_id = 'base_link'
#         transform.transform.translation.x = self.x
#         transform.transform.translation.y = self.y
#         transform.transform.translation.z = 0.0
#         transform.transform.rotation.x = qx
#         transform.transform.rotation.y = qy
#         transform.transform.rotation.z = qz
#         transform.transform.rotation.w = qw
        
#         # Send the transform
#         self.tf_broadcaster.sendTransform(transform)

# def main(args=None):
#     rclpy.init(args=args)
#     arduino_serial_node = ArduinoSerialNode()
    
#     try:
#         rclpy.spin(arduino_serial_node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         arduino_serial_node.serial_connection.close()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion, TransformStamped, Twist
from tf2_ros import TransformBroadcaster
import serial
import time
import math
from transforms3d.euler import euler2quat  # For ROS2/tf2

class ArduinoSerialNode(Node):
    def __init__(self):
        super().__init__('arduino_serial_node')
        
        # Open serial connection to Arduino
        self.serial_port = '/dev/ttyUSB1'  # or '/dev/ttyACM0' or your specific port
        self.baud_rate = 9600
        
        try:
            self.serial_connection = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f'Successfully connected to {self.serial_port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Error opening serial port: {e}')
            exit(1)
        
        # Create tf2 broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Create odometry publisher for SLAM toolbox
        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        
        # Keep original publishers
        self.encoder_publisher = self.create_publisher(Float64, 'encoder_position', 10)
        self.motor_status_publisher = self.create_publisher(String, 'motor_status', 10)
        
        # Subscribe to cmd_vel topic for teleop keyboard
        self.cmd_vel_subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.get_logger().info('Subscribed to /cmd_vel topic')
        
        # Create a timer to check for new data from Arduino
        self.timer = self.create_timer(0.1, self.read_serial_data)  # Read every 100ms
        
        # Initialize odometry values
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vtheta = 0.0

    def cmd_vel_callback(self, msg):
        """
        Handle cmd_vel messages from teleop keyboard and send to Arduino
        """
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        
        # Format command for Arduino using the 'V:' prefix as expected by your Arduino code
        command = f"V:{linear_x:.6f},{angular_z:.6f}\n"
        
        try:
            # Send the command to Arduino
            self.serial_connection.write(command.encode())
            self.get_logger().info(f'Actual command send to Arduino: {command.encode()}')
            self.get_logger().info(f'Sent velocity command to Arduino: linear={linear_x:.2f}, angular={angular_z:.2f}')
        except serial.SerialException as e:
            self.get_logger().error(f'Error sending command to Arduino: {e}')

    def read_serial_data(self):
        """
        Read and process data from Arduino
        """
        if self.serial_connection.in_waiting > 0:
            try:
                data = self.serial_connection.readline().decode('utf-8').strip()
                if data:
                    # Check if we have odometry data (x,y,theta,vx,vy,vtheta)
                    values = data.split(',')
                    if len(values) >= 6:
                        try:
                            self.x = float(values[0])
                            self.y = float(values[1])
                            self.theta = float(values[2])
                            self.vx = float(values[3])
                            self.vy = float(values[4])
                            self.vtheta = float(values[5])
                            
                            # Publish odometry data
                            self.publish_odometry()
                            
                            self.get_logger().debug(f'Published odometry: x={self.x:.2f}, y={self.y:.2f}, theta={self.theta:.2f}')
                        except ValueError as e:
                            self.get_logger().error(f'Error parsing odometry data: {data}, error: {e}')
                    
                    # If we have the original format (position,status)
                    elif len(values) == 2:
                        # try:
                        #     position_str, motor_status = values
                        #     position = float(position_str)  # Convert position to float

                        #     # Publish the encoder position
                        #     encoder_msg = Float64()
                        #     encoder_msg.data = position
                        #     self.encoder_publisher.publish(encoder_msg)
                            
                        #     # Publish the motor status
                        #     motor_status_msg = String()
                        #     motor_status_msg.data = motor_status
                        #     self.motor_status_publisher.publish(motor_status_msg)
                            
                        #     # Log the data
                        #     self.get_logger().debug(f'Received encoder position: {position}, Motor status: {motor_status}')
                        # except ValueError as e:
                        #     self.get_logger().error(f'Error parsing encoder data: {data}, error: {e}')
                        if data:
                            # First check if this is a command message (starts with V: or CMD:)
                            if data.startswith('V:') or data.startswith('CMD:'):
                                # This is a command echo, not encoder data - just log it
                                self.get_logger().debug(f'Received command echo: {data}')
                            # Check if we have odometry data (x,y,theta,vx,vy,vtheta)
                            elif len(values) >= 6:
                                try:
                                    self.x = float(values[0])
                                    # ... rest of your odometry parsing code
                                except ValueError as e:
                                    self.get_logger().error(f'Error parsing odometry data: {data}, error: {e}')
                            # If we have the original format (position,status)
                            elif len(values) == 2:
                                try:
                                    position_str, motor_status = values
                                    position = float(position_str)  # Convert position to float
                                    # ... rest of your encoder data parsing code
                                except ValueError as e:
                                    self.get_logger().error(f'Error parsing encoder data: {data}, error: {e}')
            except UnicodeDecodeError as e:
                self.get_logger().error(f'Error decoding data from Arduino: {e}')
    
    def publish_odometry(self):
        """
        Publish odometry data and transform
        """
        # Create and publish odometry message
        odom_msg = Odometry()
        now = self.get_clock().now()
        odom_msg.header.stamp = now.to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_footprint'
        
        # Set position
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        
        # Set orientation (convert theta to quaternion)
        qx, qy, qz, qw = euler2quat(0, 0, self.theta)
        odom_msg.pose.pose.orientation = Quaternion(x=qx, y=qy, z=qz, w=qw)
        
        # Set velocity
        odom_msg.twist.twist.linear.x = self.vx
        odom_msg.twist.twist.linear.y = self.vy
        odom_msg.twist.twist.angular.z = self.vtheta
        
        # Publish odometry message
        self.odom_publisher.publish(odom_msg)
        
        # Broadcast transform using tf2
        transform = TransformStamped()
        transform.header.stamp = now.to_msg()
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_footprint'
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        
        # Send the transform
        self.tf_broadcaster.sendTransform(transform)
    
    def send_reset_odometry(self):
        """
        Send command to reset odometry on Arduino
        """
        try:
            self.serial_connection.write(b"R\n")
            self.get_logger().info('Sent reset odometry command to Arduino')
        except serial.SerialException as e:
            self.get_logger().error(f'Error sending reset command: {e}')
    
    def send_direct_motor_command(self, left, right):
        """
        Send direct motor control command to Arduino
        """
        command = f"M:{left},{right}\n"
        try:
            self.serial_connection.write(command.encode())
            self.get_logger().info(f'Sent direct motor command: left={left}, right={right}')
        except serial.SerialException as e:
            self.get_logger().error(f'Error sending motor command: {e}')
    
    def send_steering_command(self, left, right):
        """
        Send steering angle command to Arduino
        """
        command = f"S:{left},{right}\n"
        try:
            self.serial_connection.write(command.encode())
            self.get_logger().info(f'Sent steering command: left={left}, right={right}')
        except serial.SerialException as e:
            self.get_logger().error(f'Error sending steering command: {e}')

def main(args=None):
    rclpy.init(args=args)
    arduino_serial_node = ArduinoSerialNode()
    
    try:
        rclpy.spin(arduino_serial_node)
    except KeyboardInterrupt:
        pass
    finally:
        # Make sure to stop motors before shutting down
        try:
            arduino_serial_node.send_direct_motor_command(0, 0)
        except:
            pass
        arduino_serial_node.serial_connection.close()
        arduino_serial_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
