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
from nav_msgs.msg import OccupancyGrid
import numpy as np
from enum import Enum
from visualization_msgs.msg import Marker, MarkerArray
import os
import yaml
from ament_index_python.packages import get_package_share_directory

# Constants for frontier detection
OCC_THRESHOLD = 10
MIN_FRONTIER_SIZE = 5

class PointClassification(Enum):
    MapOpen = 1
    MapClosed = 2
    FrontierOpen = 4
    FrontierClosed = 8

class OccupancyGrid2d():
    class CostValues(Enum):
        FreeSpace = 0
        LethalObstacle = 100
        NoInformation = -1

    def __init__(self, map_msg):
        self.map = map_msg

    def getCost(self, mx, my):
        return self.map.data[self.__getIndex(mx, my)]

    def getSize(self):
        return (self.map.info.width, self.map.info.height)

    def getSizeX(self):
        return self.map.info.width

    def getSizeY(self):
        return self.map.info.height

    def mapToWorld(self, mx, my):
        wx = self.map.info.origin.position.x + (mx + 0.5) * self.map.info.resolution
        wy = self.map.info.origin.position.y + (my + 0.5) * self.map.info.resolution
        return (wx, wy)

    def worldToMap(self, wx, wy):
        if (wx < self.map.info.origin.position.x or wy < self.map.info.origin.position.y):
            return None  # Return None for out of bounds

        mx = int((wx - self.map.info.origin.position.x) / self.map.info.resolution)
        my = int((wy - self.map.info.origin.position.y) / self.map.info.resolution)

        if (my >= self.map.info.height or mx >= self.map.info.width):
            return None  # Return None for out of bounds

        return (mx, my)

    def __getIndex(self, mx, my):
        return my * self.map.info.width + mx

class FrontierCache():
    def __init__(self):
        self.cache = {}

    def getPoint(self, x, y):
        idx = self.__cantorHash(x, y)

        if idx in self.cache:
            return self.cache[idx]

        self.cache[idx] = FrontierPoint(x, y)
        return self.cache[idx]

    def __cantorHash(self, x, y):
        return int(((x + y) * (x + y + 1)) / 2) + y

    def clear(self):
        self.cache = {}

class FrontierPoint():
    def __init__(self, x, y):
        self.classification = 0
        self.mapX = x
        self.mapY = y

def centroid(arr):
    """Calculate the centroid of a set of points."""
    arr = np.array(arr)
    length = arr.shape[0]
    sum_x = np.sum(arr[:, 0])
    sum_y = np.sum(arr[:, 1])
    return sum_x/length, sum_y/length

def findFree(mx, my, costmap):
    """Find the nearest free space from the given coordinates."""
    fCache = FrontierCache()
    bfs = [fCache.getPoint(mx, my)]

    while len(bfs) > 0:
        loc = bfs.pop(0)

        if costmap.getCost(loc.mapX, loc.mapY) == OccupancyGrid2d.CostValues.FreeSpace.value:
            return (loc.mapX, loc.mapY)

        for n in getNeighbors(loc, costmap, fCache):
            if n.classification & PointClassification.MapClosed.value == 0:
                n.classification = n.classification | PointClassification.MapClosed.value
                bfs.append(n)

    return (mx, my)

def getNeighbors(point, costmap, fCache):
    """Get the neighbors of a point in the grid."""
    neighbors = []

    for x in range(point.mapX - 1, point.mapX + 2):
        for y in range(point.mapY - 1, point.mapY + 2):
            if (x > 0 and x < costmap.getSizeX() and y > 0 and y < costmap.getSizeY()):
                neighbors.append(fCache.getPoint(x, y))

    return neighbors

def isFrontierPoint(point, costmap, fCache):
    """Check if a point is a frontier point (boundary between free and unknown space)."""
    if costmap.getCost(point.mapX, point.mapY) != OccupancyGrid2d.CostValues.NoInformation.value:
        return False

    hasFree = False
    for n in getNeighbors(point, costmap, fCache):
        cost = costmap.getCost(n.mapX, n.mapY)

        if cost > OCC_THRESHOLD:
            return False

        if cost == OccupancyGrid2d.CostValues.FreeSpace.value:
            hasFree = True

    return hasFree

def getFrontiers(current_pose, costmap, logger):
    """Get all frontier centroids from the current map."""
    fCache = FrontierCache()
    fCache.clear()

    map_coords = costmap.worldToMap(current_pose.position.x, current_pose.position.y)
    if map_coords is None:
        logger.warning('Current position is outside the map bounds')
        return []

    mx, my = map_coords

    freePoint = findFree(mx, my, costmap)
    start = fCache.getPoint(freePoint[0], freePoint[1])
    start.classification = PointClassification.MapOpen.value
    mapPointQueue = [start]

    frontiers = []

    while len(mapPointQueue) > 0:
        p = mapPointQueue.pop(0)

        if p.classification & PointClassification.MapClosed.value != 0:
            continue

        if isFrontierPoint(p, costmap, fCache):
            p.classification = p.classification | PointClassification.FrontierOpen.value
            frontierQueue = [p]
            newFrontier = []

            while len(frontierQueue) > 0:
                q = frontierQueue.pop(0)

                if q.classification & (PointClassification.MapClosed.value | PointClassification.FrontierClosed.value) != 0:
                    continue

                if isFrontierPoint(q, costmap, fCache):
                    newFrontier.append(q)

                    for w in getNeighbors(q, costmap, fCache):
                        if w.classification & (PointClassification.FrontierOpen.value | PointClassification.FrontierClosed.value | PointClassification.MapClosed.value) == 0:
                            w.classification = w.classification | PointClassification.FrontierOpen.value
                            frontierQueue.append(w)

                q.classification = q.classification | PointClassification.FrontierClosed.value

            # Extract world coordinates of frontier points
            newFrontierCords = []
            for x in newFrontier:
                x.classification = x.classification | PointClassification.MapClosed.value
                newFrontierCords.append([x.mapX, x.mapY])

            if len(newFrontier) > MIN_FRONTIER_SIZE:
                # Calculate centroid in map coordinates
                center_mx, center_my = centroid(newFrontierCords)
                # Convert to world coordinates
                wx, wy = costmap.mapToWorld(int(center_mx), int(center_my))
                frontiers.append((wx, wy))

        for v in getNeighbors(p, costmap, fCache):
            if v.classification & (PointClassification.MapOpen.value | PointClassification.MapClosed.value) == 0:
                if any(costmap.getCost(x.mapX, x.mapY) == OccupancyGrid2d.CostValues.FreeSpace.value for x in getNeighbors(v, costmap, fCache)):
                    v.classification = v.classification | PointClassification.MapOpen.value
                    mapPointQueue.append(v)

        p.classification = p.classification | PointClassification.MapClosed.value

    return frontiers

class MissionController(Node):
    def __init__(self):
        super().__init__('mission_controller')

        # Parameters
        self.declare_parameter('exploration_radius', 3.0)
        self.declare_parameter('exploration_points', 8)
        self.declare_parameter('fire_approach_distance', 0.5)
        self.declare_parameter('return_timeout', 180.0)  # seconds
        self.declare_parameter('use_frontier_exploration', True)  # New parameter

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
        self.costmap = None  # Store the latest costmap
        self.frontier_markers = []  # For visualization

        # Get parameters
        self.exploration_radius = self.get_parameter('exploration_radius').value
        self.exploration_points = self.get_parameter('exploration_points').value
        self.fire_approach_distance = self.get_parameter('fire_approach_distance').value
        self.return_timeout = self.get_parameter('return_timeout').value
        self.use_frontier_exploration = self.get_parameter('use_frontier_exploration').value

        # Navigation action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # TF listener to get robot pose
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Add map subscription for frontier detection
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10)

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

        # Add frontier visualization publisher
        self.frontier_marker_pub = self.create_publisher(
            MarkerArray,
            '/frontier_markers',
            10)

        # Add fire marker publisher
        self.fire_marker_pub = self.create_publisher(
            Marker,
            '/fire_marker',
            10)

        # Initialize timers
        self.state_timer = self.create_timer(1.0, self.state_machine_callback)
        self.pose_timer = self.create_timer(0.5, self.update_pose)
        self.status_timer = self.create_timer(0.5, self.publish_status)

        self.get_logger().info('Mission Controller initialized, waiting for navigation server...')
        self.nav_client.wait_for_server()  # Wait for the navigation server to be ready
        self.get_logger().info('Navigation server connected, ready to start mission')

        # Load any previously saved fire locations
        self.previous_fire_location = self.load_previous_fire_locations()

    def map_callback(self, msg):
        """Process incoming occupancy grid map."""
        self.costmap = OccupancyGrid2d(msg)
        self.get_logger().debug('Received updated map')

    def get_frontier_waypoints(self):
        """Generate waypoints based on frontier detection."""
        if self.costmap is None or self.current_pose is None:
            self.get_logger().warn('Cannot detect frontiers - no map or pose available')
            return []

        frontiers = getFrontiers(self.current_pose, self.costmap, self.get_logger())
        self.get_logger().info(f'Found {len(frontiers)} frontiers')

        # Visualize frontiers
        self.publish_frontier_markers(frontiers)

        return frontiers

    def publish_frontier_markers(self, frontiers):
        """Publish markers to visualize frontiers."""
        marker_array = MarkerArray()

        # Clear existing markers
        if self.frontier_markers:
            clear_marker = Marker()
            clear_marker.action = Marker.DELETEALL
            marker_array.markers.append(clear_marker)
            self.frontier_marker_pub.publish(marker_array)
            marker_array.markers.clear()

        # Create new markers
        self.frontier_markers = []
        for i, frontier in enumerate(frontiers):
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "frontiers"
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose.position.x = frontier[0]
            marker.pose.position.y = frontier[1]
            marker.pose.position.z = 0.1
            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2
            marker.color.r = 0.0
            marker.color.g = 0.0
            marker.color.b = 1.0
            marker.color.a = 1.0
            marker.lifetime.sec = 5

            self.frontier_markers.append(marker)
            marker_array.markers.append(marker)

        if marker_array.markers:
            self.frontier_marker_pub.publish(marker_array)

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
        """Generate exploration waypoints with priority for previous fire locations."""
        waypoints = []

        # If we have a previous fire location, add it as the first waypoint
        if hasattr(self, 'previous_fire_location') and self.previous_fire_location:
            x, y = self.previous_fire_location
            fire_wp = self.create_pose_stamped(x, y)
            waypoints.append(fire_wp)
            self.get_logger().info(f"Added previous fire location as first waypoint: x={x}, y={y}")

        # Then continue with normal waypoint generation (frontier or circular)
        if self.use_frontier_exploration and self.costmap is not None:
            # Use frontier-based exploration
            frontiers = self.get_frontier_waypoints()
            if frontiers:
                self.get_logger().info(f'Using {len(frontiers)} frontier waypoints for exploration')
                waypoints.extend([self.create_pose_stamped(x, y) for x, y in frontiers])
                return waypoints

        # Fallback to circular pattern
        self.get_logger().info('Using circular pattern for exploration')

        for i in range(self.exploration_points):
            angle = 2 * math.pi * i / self.exploration_points
            x = self.start_pose.pose.position.x + self.exploration_radius * math.cos(angle)
            y = self.start_pose.pose.position.y + self.exploration_radius * math.sin(angle)

            wp = self.create_pose_stamped(x, y)

            # Set orientation to face the center for better sensing
            wp.pose.orientation.z = math.sin(-angle/2)
            wp.pose.orientation.w = math.cos(-angle/2)

            waypoints.append(wp)

        self.get_logger().info(f'Generated {len(waypoints)} exploration waypoints')
        return waypoints

    def create_pose_stamped(self, x, y):
        """Helper to create a PoseStamped message."""
        wp = PoseStamped()
        wp.header.frame_id = "map"
        wp.header.stamp = self.get_clock().now().to_msg()
        wp.pose.position.x = x
        wp.pose.position.y = y
        wp.pose.orientation.w = 1.0
        return wp

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
                return

            # If we've completed the current waypoints but still exploring
            if self.current_waypoint_index >= len(self.exploration_waypoints) and not self.navigation_active:
                # Check if we should regenerate waypoints using frontier detection
                if self.use_frontier_exploration:
                    new_waypoints = self.generate_exploration_waypoints()
                    if new_waypoints:
                        self.exploration_waypoints = new_waypoints
                        self.current_waypoint_index = 0
                        self.get_logger().info('Regenerated frontier waypoints for continued exploration')
                    else:
                        # No more frontiers, mission complete
                        self.state = "RETURNING"
                        self.get_logger().info('No more frontiers to explore, returning to start')
                else:
                    # Using fixed waypoints - check time constraints
                    elapsed_time = (self.get_clock().now() - self.mission_start_time).nanoseconds / 1e9

                    if elapsed_time > self.return_timeout:
                        self.state = "RETURNING"
                        self.get_logger().info('Time limit reached, returning to start without fire detection')
                    else:
                        # Reset for another exploration pass
                        self.current_waypoint_index = 0
                        self.get_logger().info('First exploration pass complete, starting second pass')

            # Continue with exploration waypoints
            elif self.current_waypoint_index < len(self.exploration_waypoints) and not self.navigation_active:
                self.send_navigation_goal(self.exploration_waypoints[self.current_waypoint_index])

        elif self.state == "APPROACHING_FIRE":
            # Send goal to move to the fire
            if not self.navigation_active:
                self.send_navigation_goal(self.fire_location)
                self.state = "AT_FIRE"

        elif self.state == "AT_FIRE":
            # Wait until navigation is done
            if not self.navigation_active:
                self.get_logger().info('Reached fire location, confirming position')

                # Mark the fire location visually
                self.mark_fire_location()

                # Save the fire location to file for future rounds
                self.save_fire_location()

                # Continue to return to start
                self.state = "RETURNING"
                self.get_logger().info('Fire location marked and saved, returning to start')

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

    def mark_fire_location(self):
        """Create a visual marker at the fire location."""
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "fire_detection"
        marker.id = 0
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        # Set the position to the fire location
        marker.pose.position.x = self.fire_location.pose.position.x
        marker.pose.position.y = self.fire_location.pose.position.y
        marker.pose.position.z = 0.0

        # Set the orientation (standing cylinder)
        marker.pose.orientation.w = 1.0

        # Set size
        marker.scale.x = 0.3  # 30cm diameter
        marker.scale.y = 0.3
        marker.scale.z = 0.5  # 50cm tall

        # Set color (bright red-orange for fire)
        marker.color.r = 1.0
        marker.color.g = 0.3
        marker.color.b = 0.0
        marker.color.a = 1.0

        # Make it permanent
        marker.lifetime.sec = 0  # 0 = forever

        # Publish the marker
        self.fire_marker_pub.publish(marker)
        self.get_logger().info(f"Published fire marker at x={self.fire_location.pose.position.x}, y={self.fire_location.pose.position.y}")

    def save_fire_location(self):
        """Save the fire location to a file for use in future rounds."""
        # Get current time for the filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        # Create the fire data
        fire_data = {
            'fire_location': {
                'x': float(self.fire_location.pose.position.x),
                'y': float(self.fire_location.pose.position.y),
                'frame_id': 'map',
                'detected_time': timestamp
            }
        }

        # Create directory for fire locations if it doesn't exist
        maps_dir = os.path.join(get_package_share_directory('autobot_core'), 'maps')
        os.makedirs(maps_dir, exist_ok=True)

        # Save to file
        fire_file = os.path.join(maps_dir, f"fire_location_{timestamp}.yaml")
        with open(fire_file, 'w') as f:
            yaml.dump(fire_data, f, default_flow_style=False)

        # Also save to a fixed location that will be overwritten each time
        latest_file = os.path.join(maps_dir, "latest_fire_location.yaml")
        with open(latest_file, 'w') as f:
            yaml.dump(fire_data, f, default_flow_style=False)

        self.get_logger().info(f"Saved fire location to {fire_file}")
        self.get_logger().info(f"Also saved to {latest_file} for easy access")

    def load_previous_fire_locations(self):
        """Load fire locations from previous rounds."""
        maps_dir = os.path.join(get_package_share_directory('autobot_core'), 'maps')
        latest_file = os.path.join(maps_dir, "latest_fire_location.yaml")

        if os.path.exists(latest_file):
            try:
                with open(latest_file, 'r') as f:
                    fire_data = yaml.safe_load(f)

                fire_x = fire_data['fire_location']['x']
                fire_y = fire_data['fire_location']['y']

                self.get_logger().info(f"Loaded previous fire location: x={fire_x}, y={fire_y}")

                # Create a marker for the previous fire location
                self.create_previous_fire_marker(fire_x, fire_y)

                return (fire_x, fire_y)
            except Exception as e:
                self.get_logger().error(f"Error loading previous fire location: {e}")

        return None

    def create_previous_fire_marker(self, x, y):
        """Create a marker for a previously detected fire."""
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "previous_fire"
        marker.id = 1
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        marker.pose.position.x = x
        marker.pose.position.y = y
        marker.pose.position.z = 0.0
        marker.pose.orientation.w = 1.0

        # Make it slightly different from current fire marker
        marker.scale.x = 0.4
        marker.scale.y = 0.4
        marker.scale.z = 0.2

        # Make it blue to distinguish from current fire
        marker.color.r = 0.0
        marker.color.g = 0.3
        marker.color.b = 1.0
        marker.color.a = 0.7

        marker.lifetime.sec = 0

        self.fire_marker_pub.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = MissionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
