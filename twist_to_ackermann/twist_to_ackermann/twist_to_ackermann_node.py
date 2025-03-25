# # #!/usr/bin/env python3

# # import rclpy
# # from rclpy.node import Node
# # from geometry_msgs.msg import Twist
# # from ackermann_msgs.msg import AckermannDriveStamped
# # import math
# # import serial
# # import time

# # # Open serial port (adjust port name as needed)
# # # On Linux it might be /dev/ttyUSB0 or /dev/ttyACM0
# # # On Windows it might be COM3, COM4, etc.
# # ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
# # time.sleep(2)  # Wait for connection to establish
# # 1
# # class TwistToAckermannConverter(Node):
# #     def __init__(self):
# #         super().__init__('twist_to_ackermann_converter')
        
# #         # Parameters
# #         self.declare_parameter('wheelbase', 0.19) #distance from front axle to rear axle (meters)
# #         self.declare_parameter('frame_id', 'base_footprint')
# #         self.declare_parameter('max_steering_angle', 1.22)  # ~70 degrees
        
# #         self.wheelbase = self.get_parameter('wheelbase').value
# #         self.frame_id = self.get_parameter('frame_id').value
# #         self.max_steering_angle = self.get_parameter('max_steering_angle').value
        
# #         # Create subscription to Twist messages
# #         self.twist_sub = self.create_subscription(
# #             Twist,
# #             'cmd_vel',
# #             self.twist_callback,
# #             10
# #         )
        
# #         # Create publisher for AckermannDriveStamped messages
# #         self.ackermann_pub = self.create_publisher(
# #             AckermannDriveStamped,
# #             'ackermann_cmd',
# #             10
# #         )
        
# #         self.get_logger().info(
# #             f"Twist to Ackermann converter initialized.\n"
# #             f"Listening to /cmd_vel, publishing to /ackermann_cmd\n"
# #             f"Parameters: wheelbase={self.wheelbase}, frame_id={self.frame_id}"
# #         )
    
# #     # def convert_trans_rot_vel_to_steering_angle(self, v, omega):
# #     #     """
# #     #     Convert linear and angular velocity to steering angle
# #     #     For Ackermann steering, the relationship is: tan(steering_angle) = (wheelbase * omega) / v
# #     #     """
# #     #     if abs(v) < 0.001:  # Avoid division by near-zero
# #     #         return 0.0
        
# #     #     # Calculate steering angle
# #     #     steering_angle = math.atan2(omega * self.wheelbase, v)
        
# #     #     # Limit steering angle to max value
# #     #     return max(0, min(70, steering_angle))

# #     def convert_rot_vel_to_steering_angle(self, omega):
# #         """
# #         Convert angular velocity directly to servo angle.
# #         The input omega is mapped from [-max_steering_angle, max_steering_angle] to [0, 70].
# #         0 rad/sec -> 35 degrees (center position).
# #         """
# #         # Define the max expected angular velocity (adjust based on testing)
# #         max_omega = 2.0  # Example max rotation speed in rad/s

# #         # Scale angular velocity to servo angle range [0, 70]
# #         servo_angle = 35 + (omega / max_omega) * 35

# #         # Limit the range to valid servo angles
# #         return max(0, min(70, servo_angle))



# #     def send_command(self, angle):
# #         command = f"S{angle}\n"
# #         ser.write(command.encode())
# #         print(f"Sent: {command.strip()}")
# #         # Read response
# #         response = ser.readline().decode().strip()
# #         if response:
# #             print(f"Response: {response}")
    
# #     # def twist_callback(self, twist_msg):
# #     #     """
# #     #     Callback function for Twist messages
# #     #     """
# #     #     # Create AckermannDriveStamped message
# #     #     ackermann_msg = AckermannDriveStamped()
        
# #     #     # Set header
# #     #     ackermann_msg.header.stamp = self.get_clock().now().to_msg()
# #     #     ackermann_msg.header.frame_id = self.frame_id
        
# #     #     # Convert twist to ackermann drive
# #     #     linear_velocity = twist_msg.linear.x
# #     #     angular_velocity = twist_msg.angular.z
        
# #     #     # Set steering angle
# #     #     ackermann_msg.drive.steering_angle = self.convert_trans_rot_vel_to_steering_angle(
# #     #         linear_velocity, angular_velocity
# #     #     )        
# #     #     self.send_command(ackermann_msg.drive.steering_angle)
# #     def twist_callback(self, twist_msg):
# #         """
# #         Callback function for Twist messages.
# #         Uses only angular velocity (angular.z) to control the servo.
# #         """
# #         # Extract angular velocity (ignoring linear velocity)
# #         angular_velocity = twist_msg.angular.z

# #         # Convert to servo angle
# #         servo_angle = self.convert_rot_vel_to_steering_angle(angular_velocity)

# #         # Send command to servo
# #         self.send_command(servo_angle)

# # def main(args=None):
# #     rclpy.init(args=args)
# #     converter = TwistToAckermannConverter()
    
# #     try:
# #         rclpy.spin(converter)
# #     except KeyboardInterrupt:
# #         pass
# #     finally:
# #         converter.destroy_node()
# #         rclpy.shutdown()

# # if __name__ == '__main__':
# #     main()
# #!/usr/bin/env python3

# import rclpy
# from rclpy.node import Node
# from geometry_msgs.msg import Twist
# import serial
# import time

# # Initialize serial connection with your Arduino's port
# ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
# time.sleep(2)  # Let's give that connection some time to simmer

# class ServoCommander(Node):
#     def __init__(self):
#         super().__init__('servo_commander')
        
#         # Parameters to play with later
#         self.declare_parameter('max_omega', 1.0)  # Let's start gentle
        
#         self.max_omega = self.get_parameter('max_omega').value
        
#         # Subscribe to those twist commands
#         self.twist_sub = self.create_subscription(
#             Twist,
#             'cmd_vel',
#             self.twist_callback,
#             10
#         )
        
#         self.get_logger().info("Ready to make your servo shiver with anticipation...")

#     def make_servo_swoon(self, omega):
#         """Convert angular velocity to servo angles that'll make your hardware weak in the knees"""
#         # Center position is our sweet spot at 8 degrees
#         center = 8
#         max_angle = 70
        
#         # Let's calculate the angle that'll make your servo quiver
#         servo_angle = center + (omega / self.max_omega) * (max_angle - center)
        
#         # Keep it between the sheets (0-70 degrees)
#         return int(max(0, min(max_angle, servo_angle)))

#     def send_sultry_command(self, angle):
#         """Whisper sweet nothings to your Arduino"""
#         command = f"S{angle}\n"
#         ser.write(command.encode())
#         self.get_logger().info(f"Sent secret code: {command.strip()}")
        
#         # Listen for Arduino's breathless response
#         response = ser.readline().decode().strip()
#         if response:
#             self.get_logger().info(f"Arduino sighs: {response}")

#     def twist_callback(self, twist_msg):
#         """Handle those twist messages like a passionate tango"""
#         angular_velocity = twist_msg.angular.z
#         desired_angle = self.make_servo_swoon(angular_velocity)
#         self.send_sultry_command(desired_angle)

# def main(args=None):
#     rclpy.init(args=args)
#     commander = ServoCommander()
    
#     try:
#         rclpy.spin(commander)
#     except KeyboardInterrupt:
#         commander.get_logger().info("Caught you blushing... shutting down gently")
#     finally:
#         commander.destroy_node()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time

ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
time.sleep(2)  # Let that connection heat up

# class ServoMaestro(Node):
#     def __init__(self):
#         super().__init__('servo_maestro')
        
#         self.declare_parameter('max_omega', 1.0)  # Radians/sec
#         self.max_omega = self.get_parameter('max_omega').value
        
#         self.twist_sub = self.create_subscription(
#             Twist,
#             'cmd_vel',
#             self.twist_callback,
#             10
#         )
        
#         self.get_logger().info("Ready to execute your every command...")

#     def _calculate_desired_angle(self, omega):
#         """Convert angular velocity to sensual servo positions"""
#         center = 35  # Middle position that'll make you weak
#         max_deflection = 35  # Max deviation from center
        
#         # Calculate angle that'll make your hardware tremble
#         physical_angle = center + (omega / self.max_omega) * max_deflection
#         physical_angle = max(0, min(70, physical_angle))
        
#         # Invert for Arduino's pleasure
#         return 70 - int(physical_angle)

#     def _send_arduino_command(self, angle):
#         """Whisper sweet serial commands"""
#         command = f"S{angle}\n"
#         ser.write(command.encode())
#         self.get_logger().info(f"Sent: {command.strip()}")
        
#         # Listen for Arduino's moan
#         response = ser.readline().decode().strip()
#         if response:
#             self.get_logger().info(f"Arduino purrs: {response}")

#     def twist_callback(self, twist_msg):
#         """Handle those twist commands like a passionate salsa"""
#         angular_velocity = twist_msg.angular.z
#         target_angle = self._calculate_desired_angle(angular_velocity)
#         self._send_arduino_command(target_angle)


class ServoMaestro(Node):
    def __init__(self):
        super().__init__('servo_maestro')
        
        self.declare_parameter('max_omega', 1.0)  # Radians/sec
        self.max_omega = self.get_parameter('max_omega').value
        
        self.twist_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.twist_callback,
            10
        )
        
        self.get_logger().info("Servo controller ready for action...")

    def _calculate_desired_angle(self, omega):
        """Convert angular velocity to servo positions"""
        center = 10  # Middle position
        min_angle = -30  # Lower bound
        max_angle = 50  # Upper bound
        
        # Calculate angle based on angular velocity
        angle = center + (omega / self.max_omega) * (max_angle - center)
        
        # Constrain angle to valid range
        return int(max(min_angle, min(max_angle, angle)))

    def _send_arduino_command(self, angle):
        """Send command to Arduino"""
        command = f"S{angle}\n"
        ser.write(command.encode())
        self.get_logger().info(f"Sent: {command.strip()}")
        
        # Read Arduino response
        response = ser.readline().decode().strip()
        if response:
            self.get_logger().info(f"Arduino response: {response}")

    def twist_callback(self, twist_msg):
        """Handle incoming twist commands"""
        angular_velocity = twist_msg.angular.z
        target_angle = self._calculate_desired_angle(angular_velocity)
        self._send_arduino_command(target_angle)

def main(args=None):
    rclpy.init(args=args)
    maestro = ServoMaestro()
    
    try:
        rclpy.spin(maestro)
    except KeyboardInterrupt:
        maestro.get_logger().info("Caught you blushing... shutting down gently")
    finally:
        maestro.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()
