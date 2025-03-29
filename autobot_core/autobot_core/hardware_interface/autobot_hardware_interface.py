import rclpy
from rclpy.node import Node
import serial
import threading
import time
from hardware_interface import SystemInterface
from hardware_interface import HardwareInfo
from rclpy.parameter import Parameter

class AutobotHardwareInterface(SystemInterface):
    def __init__(self, hardware_info):
        super().__init__(hardware_info)
        self.joint_positions = {}
        self.joint_velocities = {}
        self.joint_commands = {}
        
        # Initialize serial connection
        self.serial_port = None
        self.serial_available = False
        
        # Extract parameters from hardware_info
        self.serial_device = self.get_parameter_or_default(hardware_info, 'serial_port', '/dev/ttyUSB2')
        self.baud_rate = int(self.get_parameter_or_default(hardware_info, 'baud_rate', '115200'))
        
        # Initialize joint state storage
        for joint in hardware_info.joints:
            joint_name = joint.name
            self.joint_positions[joint_name] = 0.0
            self.joint_velocities[joint_name] = 0.0
            
            if any(cmd.name == 'position' for cmd in joint.command_interfaces):
                self.joint_commands[joint_name] = {'position': 0.0}
            
            if any(cmd.name == 'velocity' for cmd in joint.command_interfaces):
                if joint_name not in self.joint_commands:
                    self.joint_commands[joint_name] = {}
                self.joint_commands[joint_name]['velocity'] = 0.0
        
        # Store Ackermann-specific joint names for easier access
        self.left_rear_wheel = 'left_rear_wheel_joint'
        self.right_rear_wheel = 'right_rear_wheel_joint'
        self.left_front_wheel = 'front_left_wheel_joint'
        self.right_front_wheel = 'front_right_wheel_joint'
        self.left_steering = 'front_left_pivot_joint'
        self.right_steering = 'front_right_pivot_joint'
    
    def get_parameter_or_default(self, hardware_info, param_name, default_value):
        for param in hardware_info.hardware_parameters:
            if param.name == param_name:
                return param.value
        return default_value
    
    def on_init(self, hardware_info):
        # Connect to serial port
        try:
            self.serial_port = serial.Serial(
                self.serial_device,
                self.baud_rate,
                timeout=1.0
            )
            self.serial_available = True
            print(f"Connected to {self.serial_device}")
            
            # Send initialization command to hardware
            self.serial_port.reset_input_buffer()
            self.serial_port.write(b"INIT:ACKERMANN\n")
            time.sleep(0.1)  # Give hardware time to process
            
        except serial.SerialException as e:
            print(f"Failed to open serial port: {e}")
            self.serial_available = False
        
        return True
    
    def read(self):
        # Read joint states from hardware (ESP32/Arduino)
        if self.serial_available:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                    
                    # Handle different message types from hardware
                    if line.startswith("JOINT_STATE:"):
                        # Parse joint state data from serial
                        # Format: "JOINT_STATE:joint_name,position,velocity"
                        data = line.split(':')[1].split(',')
                        if len(data) >= 3:
                            joint_name = data[0]
                            position = float(data[1])
                            velocity = float(data[2])
                            
                            if joint_name in self.joint_positions:
                                self.joint_positions[joint_name] = position
                                self.joint_velocities[joint_name] = velocity
                    
                    elif line.startswith("ODOM:"):
                        # Parse odometry data if provided by hardware
                        # This can be used to update wheel positions/velocities
                        # Format: "ODOM:x,y,theta,vx,vy,vtheta"
                        data = line.split(':')[1].split(',')
                        if len(data) >= 6:
                            # Update wheel positions based on odometry if needed
                            pass
            except Exception as e:
                print(f"Error reading from serial: {e}")
        
        return True
    
    def write(self):
        # Send commands to hardware (ESP32/Arduino)
        if self.serial_available:
            try:
                # Format steering commands - use left steering as primary
                steering_cmd = 0.0
                if self.left_steering in self.joint_commands and 'position' in self.joint_commands[self.left_steering]:
                    steering_cmd = self.joint_commands[self.left_steering]['position']
                
                # Format velocity commands - use left rear wheel as primary
                velocity_cmd = 0.0
                if self.left_rear_wheel in self.joint_commands and 'velocity' in self.joint_commands[self.left_rear_wheel]:
                    velocity_cmd = self.joint_commands[self.left_rear_wheel]['velocity']
                
                # Send Ackermann command to hardware
                command = f"ACKERMANN:{velocity_cmd:.4f},{steering_cmd:.4f}\n"
                self.serial_port.write(command.encode())
                
                # Optional: Add debug output if needed
                # print(f"Sent: {command.strip()}")
                
            except Exception as e:
                print(f"Error writing to serial: {e}")
        
        return True
    
    def get_position_interfaces(self):
        return self.joint_positions
    
    def get_velocity_interfaces(self):
        return self.joint_velocities
    
    def set_command_interface_position(self, joint_name, position):
        if joint_name in self.joint_commands and 'position' in self.joint_commands[joint_name]:
            self.joint_commands[joint_name]['position'] = position
    
    def set_command_interface_velocity(self, joint_name, velocity):
        if joint_name in self.joint_commands and 'velocity' in self.joint_commands[joint_name]:
            self.joint_commands[joint_name]['velocity'] = velocity

def main(args=None):
    rclpy.init(args=args)
    node = AutobotHardwareInterface()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()