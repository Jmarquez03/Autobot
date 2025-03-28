#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import numpy as np
import psutil
import os
import time
from datetime import datetime

# Message imports
from sensor_msgs.msg import LaserScan, Imu, Temperature, BatteryState
from nav_msgs.msg import Odometry
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from std_msgs.msg import Float32, String, Header, Bool


class HardwareDiagnosticsNode(Node):
    def __init__(self):
        super().__init__('hardware_diagnostics_node')
        
        # QoS profile for diagnostics
        diagnostic_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Initialize component status tracking
        self.lidar_status = {"status": "UNKNOWN", "last_update": 0, "data_quality": 0.0, "scan_count": 0}
        self.imu_status = {"status": "UNKNOWN", "last_update": 0, "data_quality": 0.0, "msg_count": 0, "temperature": 0.0}
        self.esp32_status = {"status": "UNKNOWN", "last_update": 0, "odom_quality": 0.0, "msg_count": 0}
        self.system_status = {"cpu_temp": 0.0, "cpu_percent": 0.0, "memory_percent": 0.0, "disk_percent": 0.0}
        self.navigation_status = {"status": "UNKNOWN", "mode": "UNKNOWN"}
        self.mission_status = {"status": "UNKNOWN", "fire_detected": False, "time_elapsed": 0.0}
        
        # Set up publishers
        self.diag_pub = self.create_publisher(
            DiagnosticArray,
            '/diagnostics',
            diagnostic_qos
        )
        
        self.diag_summary_pub = self.create_publisher(
            String,
            '/diagnostics_summary',
            10
        )
        
        # Set up subscribers
        # LiDAR
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        # IMU
        self.imu_sub = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )
        
        # Odometry (ESP32)
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        # Temperature sensor or fire detection
        self.temp_sub = self.create_subscription(
            Temperature,
            '/thermal_sensor/temperature',
            self.temp_callback,
            10
        )
        
        # Mission status
        self.mission_sub = self.create_subscription(
            String,
            '/mission_status',
            self.mission_callback,
            10
        )
        
        # Fire detection
        self.fire_sub = self.create_subscription(
            Bool,
            '/fire_detection',
            self.fire_callback,
            10
        )
        
        # Optional: Battery state if available
        self.battery_sub = self.create_subscription(
            BatteryState,
            '/battery_state',
            self.battery_callback,
            10
        )
        
        # Create timers
        self.diag_timer = self.create_timer(1.0, self.publish_diagnostics)
        self.system_timer = self.create_timer(5.0, self.update_system_stats)
        
        # Node start time for uptime calculation
        self.start_time = time.time()
        
        # Optional battery status (may not be available)
        self.battery_status = {"voltage": 0.0, "current": 0.0, "percentage": 0.0, "status": "UNKNOWN"}
        
        self.get_logger().info('Hardware Diagnostics Node initialized')
    
    def scan_callback(self, msg):
        # Update LiDAR status
        now = time.time()
        
        # Calculate data quality based on number of valid ranges
        valid_ranges = sum(1 for r in msg.ranges if r > 0.0 and r < msg.range_max)
        total_ranges = len(msg.ranges)
        quality = valid_ranges / total_ranges if total_ranges > 0 else 0.0
        
        self.lidar_status = {
            "status": "OK" if quality > 0.5 else "DEGRADED",
            "last_update": now,
            "data_quality": quality,
            "scan_count": self.lidar_status["scan_count"] + 1,
            "field_of_view": msg.angle_max - msg.angle_min,
            "range_min": msg.range_min,
            "range_max": msg.range_max
        }
    
    def imu_callback(self, msg):
        # Update IMU status
        now = time.time()
        
        # Check if orientation quaternion is normalized
        quat_norm = np.sqrt(
            msg.orientation.x**2 + 
            msg.orientation.y**2 + 
            msg.orientation.z**2 + 
            msg.orientation.w**2
        )
        
        # Calculate data quality
        quality = 1.0 if abs(quat_norm - 1.0) < 0.01 else max(0.0, 1.0 - abs(quat_norm - 1.0))
        
        self.imu_status = {
            "status": "OK" if quality > 0.9 else "DEGRADED",
            "last_update": now,
            "data_quality": quality,
            "msg_count": self.imu_status["msg_count"] + 1,
            "quat_norm": quat_norm
        }
    
    def odom_callback(self, msg):
        # Update ESP32/odometry status
        now = time.time()
        
        # Simple quality measure - can be improved based on actual data
        self.esp32_status = {
            "status": "OK",
            "last_update": now,
            "msg_count": self.esp32_status["msg_count"] + 1,
            "velocity_linear": msg.twist.twist.linear.x,
            "velocity_angular": msg.twist.twist.angular.z
        }
    
    def temp_callback(self, msg):
        # Update temperature status
        self.imu_status["temperature"] = msg.temperature
    
    def mission_callback(self, msg):
        # Parse mission status message
        self.mission_status["status"] = msg.data
        
        # Extract additional information from the status message
        if "TIME:" in msg.data:
            time_str = msg.data.split("TIME:")[1].split("s")[0].strip()
            try:
                self.mission_status["time_elapsed"] = float(time_str)
            except ValueError:
                pass
    
    def fire_callback(self, msg):
        # Update fire detection status
        self.mission_status["fire_detected"] = msg.data
    
    def battery_callback(self, msg):
        # Update battery status if available
        self.battery_status = {
            "voltage": msg.voltage,
            "current": msg.current,
            "percentage": msg.percentage,
            "status": "OK" if msg.percentage > 20.0 else "LOW"
        }
    
    def update_system_stats(self):
        # Update Raspberry Pi system stats
        try:
            # CPU temperature (on Raspberry Pi)
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    self.system_status["cpu_temp"] = float(f.read().strip()) / 1000.0
            
            # CPU usage
            self.system_status["cpu_percent"] = psutil.cpu_percent()
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_status["memory_percent"] = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_status["disk_percent"] = disk.percent
            
        except Exception as e:
            self.get_logger().warning(f"Failed to update system stats: {e}")
    
    def publish_diagnostics(self):
        now = time.time()
        
        # Create diagnostic array message
        diag_array = DiagnosticArray()
        diag_array.header = Header()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        
        # Add LiDAR diagnostics
        lidar_diag = DiagnosticStatus()
        lidar_diag.name = "SLLIDAR"
        lidar_diag.hardware_id = "lidar"
        
        # Determine status based on last update time and data quality
        if now - self.lidar_status["last_update"] > 2.0:
            lidar_diag.level = DiagnosticStatus.ERROR
            lidar_diag.message = "No recent data"
        elif self.lidar_status["data_quality"] < 0.5:
            lidar_diag.level = DiagnosticStatus.WARN
            lidar_diag.message = "Poor data quality"
        else:
            lidar_diag.level = DiagnosticStatus.OK
            lidar_diag.message = "OK"
        
        # Add values
        lidar_diag.values.append(KeyValue(key="data_quality", value=str(round(self.lidar_status["data_quality"], 2))))
        lidar_diag.values.append(KeyValue(key="scan_count", value=str(self.lidar_status["scan_count"])))
        if "field_of_view" in self.lidar_status:
            lidar_diag.values.append(KeyValue(key="field_of_view", value=str(round(self.lidar_status["field_of_view"], 2))))
        
        # Add IMU diagnostics
        imu_diag = DiagnosticStatus()
        imu_diag.name = "BNO055 IMU"
        imu_diag.hardware_id = "imu"
        
        if now - self.imu_status["last_update"] > 2.0:
            imu_diag.level = DiagnosticStatus.ERROR
            imu_diag.message = "No recent data"
        elif self.imu_status["data_quality"] < 0.9:
            imu_diag.level = DiagnosticStatus.WARN
            imu_diag.message = "Poor data quality"
        else:
            imu_diag.level = DiagnosticStatus.OK
            imu_diag.message = "OK"
        
        # Add values
        imu_diag.values.append(KeyValue(key="data_quality", value=str(round(self.imu_status["data_quality"], 2))))
        imu_diag.values.append(KeyValue(key="msg_count", value=str(self.imu_status["msg_count"])))
        imu_diag.values.append(KeyValue(key="temperature", value=str(round(self.imu_status["temperature"], 1))))
        if "quat_norm" in self.imu_status:
            imu_diag.values.append(KeyValue(key="quaternion_norm", value=str(round(self.imu_status["quat_norm"], 4))))
        
        # Add ESP32 diagnostics
        esp32_diag = DiagnosticStatus()
        esp32_diag.name = "ESP32 Controller"
        esp32_diag.hardware_id = "esp32"
        
        if now - self.esp32_status["last_update"] > 2.0:
            esp32_diag.level = DiagnosticStatus.ERROR
            esp32_diag.message = "No recent data"
        else:
            esp32_diag.level = DiagnosticStatus.OK
            esp32_diag.message = "OK"
        
        # Add values
        esp32_diag.values.append(KeyValue(key="msg_count", value=str(self.esp32_status["msg_count"])))
        if "velocity_linear" in self.esp32_status:
            esp32_diag.values.append(KeyValue(key="velocity_linear", value=str(round(self.esp32_status["velocity_linear"], 2))))
        if "velocity_angular" in self.esp32_status:
            esp32_diag.values.append(KeyValue(key="velocity_angular", value=str(round(self.esp32_status["velocity_angular"], 2))))
        
        # Add System diagnostics
        system_diag = DiagnosticStatus()
        system_diag.name = "Raspberry Pi System"
        system_diag.hardware_id = "raspberry_pi"
        
        # CPU temperature threshold for Raspberry Pi
        if self.system_status["cpu_temp"] > 80.0:
            system_diag.level = DiagnosticStatus.ERROR
            system_diag.message = "CPU temperature critical"
        elif self.system_status["cpu_temp"] > 70.0:
            system_diag.level = DiagnosticStatus.WARN
            system_diag.message = "CPU temperature high"
        elif self.system_status["cpu_percent"] > 90.0:
            system_diag.level = DiagnosticStatus.WARN
            system_diag.message = "CPU usage high"
        elif self.system_status["memory_percent"] > 90.0:
            system_diag.level = DiagnosticStatus.WARN
            system_diag.message = "Memory usage high"
        else:
            system_diag.level = DiagnosticStatus.OK
            system_diag.message = "OK"
        
        # Add values
        system_diag.values.append(KeyValue(key="cpu_temp", value=str(round(self.system_status["cpu_temp"], 1))))
        system_diag.values.append(KeyValue(key="cpu_percent", value=str(round(self.system_status["cpu_percent"], 1))))
        system_diag.values.append(KeyValue(key="memory_percent", value=str(round(self.system_status["memory_percent"], 1))))
        system_diag.values.append(KeyValue(key="disk_percent", value=str(round(self.system_status["disk_percent"], 1))))
        system_diag.values.append(KeyValue(key="uptime", value=str(round(now - self.start_time, 0))))
        
        # Add mission status diagnostics
        mission_diag = DiagnosticStatus()
        mission_diag.name = "Mission Status"
        mission_diag.hardware_id = "mission"
        mission_diag.level = DiagnosticStatus.OK
        mission_diag.message = self.mission_status["status"]
        
        # Add values
        mission_diag.values.append(KeyValue(key="fire_detected", value=str(self.mission_status["fire_detected"])))
        mission_diag.values.append(KeyValue(key="time_elapsed", value=str(round(self.mission_status["time_elapsed"], 1))))
        
        # Add battery status if available
        if self.battery_status["voltage"] > 0:
            battery_diag = DiagnosticStatus()
            battery_diag.name = "Battery"
            battery_diag.hardware_id = "battery"
            
            if self.battery_status["percentage"] < 10.0:
                battery_diag.level = DiagnosticStatus.ERROR
                battery_diag.message = "Battery critically low"
            elif self.battery_status["percentage"] < 20.0:
                battery_diag.level = DiagnosticStatus.WARN
                battery_diag.message = "Battery low"
            else:
                battery_diag.level = DiagnosticStatus.OK
                battery_diag.message = "OK"
            
            battery_diag.values.append(KeyValue(key="voltage", value=str(round(self.battery_status["voltage"], 2))))
            battery_diag.values.append(KeyValue(key="current", value=str(round(self.battery_status["current"], 2))))
            battery_diag.values.append(KeyValue(key="percentage", value=str(round(self.battery_status["percentage"], 1))))
            
            diag_array.status.append(battery_diag)
        
        # Add all diagnostics to array
        diag_array.status.append(lidar_diag)
        diag_array.status.append(imu_diag)
        diag_array.status.append(esp32_diag)
        diag_array.status.append(system_diag)
        diag_array.status.append(mission_diag)
        
        # Publish diagnostics
        self.diag_pub.publish(diag_array)
        
        # Create and publish a simple summary string
        summary = self.create_summary(diag_array)
        summary_msg = String()
        summary_msg.data = summary
        self.diag_summary_pub.publish(summary_msg)
        
    def create_summary(self, diag_array):
        # Create a simple text summary of diagnostics for console display
        summary_lines = []
        timestamp = datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
        summary_lines.append(f"=== ROBOT DIAGNOSTICS ({timestamp}) ===")
        
        # Check overall system status
        errors = sum(1 for status in diag_array.status if status.level == DiagnosticStatus.ERROR)
        warnings = sum(1 for status in diag_array.status if status.level == DiagnosticStatus.WARN)
        
        if errors > 0:
            summary_lines.append(f"SYSTEM STATUS: ERROR ({errors} errors, {warnings} warnings)")
        elif warnings > 0:
            summary_lines.append(f"SYSTEM STATUS: WARNING ({warnings} warnings)")
        else:
            summary_lines.append("SYSTEM STATUS: OK")
        
        # Add hardware component statuses
        for status in diag_array.status:
            status_text = "OK" if status.level == DiagnosticStatus.OK else "WARNING" if status.level == DiagnosticStatus.WARN else "ERROR"
            summary_lines.append(f"{status.name}: {status_text} - {status.message}")
        
        # Add mission specifics
        if self.mission_status["fire_detected"]:
            summary_lines.append("FIRE DETECTED: YES")
        
        summary_lines.append(f"Mission Time: {round(self.mission_status['time_elapsed'], 1)}s")
        summary_lines.append(f"System Uptime: {round(time.time() - self.start_time, 0)}s")
        
        # Add system stats
        summary_lines.append(f"CPU: {round(self.system_status['cpu_percent'], 1)}% @ {round(self.system_status['cpu_temp'], 1)}°C")
        summary_lines.append(f"Memory: {round(self.system_status['memory_percent'], 1)}%")
        
        return "\n".join(summary_lines)


def main(args=None):
    rclpy.init(args=args)
    node = HardwareDiagnosticsNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main() 