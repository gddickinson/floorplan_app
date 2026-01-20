"""
RoomPlan JSON Importer for Floor Plan Editor - FIXED VERSION

Imports 3D room scans from iPhone LiDAR/RoomPlan into 2D floor plans.
Converts meters to inches, extracts 2D footprint from 3D data.

FIXES:
- Corrected wall ordering algorithm to properly sequence walls in a closed loop
- Fixed matrix interpretation (uses row 0 for direction vector)
- Improved corner snapping and connection detection
"""

import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from core import (
    FloorPlan, Building, Point, Wall, Opening, 
    WallType, OpeningType, Furniture, FurnitureType,
    Fixture, FixtureType
)

logger = logging.getLogger(__name__)


class RoomPlanImporter:
    """Import RoomPlan JSON data into FloorPlan objects."""
    
    # Conversion factor: meters to inches
    METERS_TO_INCHES = 39.3701
    
    # Category mapping from RoomPlan to FloorPlan
    FURNITURE_MAPPING = {
        'table': FurnitureType.TABLE_DINING,
        'chair': FurnitureType.CHAIR,
        'sofa': FurnitureType.SOFA,
        'bed': FurnitureType.BED_QUEEN,  # Default to queen
        'storage': FurnitureType.CABINET,
        'desk': FurnitureType.DESK,
    }
    
    FIXTURE_MAPPING = {
        'toilet': FixtureType.TOILET,
        'sink': FixtureType.SINK,
        'bathtub': FixtureType.BATHTUB,
        'shower': FixtureType.SHOWER,
        'refrigerator': FixtureType.REFRIGERATOR,
        'stove': FixtureType.STOVE,
        'oven': FixtureType.OVEN,
        'dishwasher': FixtureType.DISHWASHER,
        'washer': FixtureType.WASHER,
        'dryer': FixtureType.DRYER,
    }
    
    def __init__(self, corner_snap_tolerance: float = 6.0):
        """
        Initialize RoomPlan importer.
        
        Args:
            corner_snap_tolerance: Distance in inches within which to snap corners together
        """
        self.scale_factor = self.METERS_TO_INCHES
        self.corner_snap_tolerance = corner_snap_tolerance
    
    def import_from_file(self, filepath: str) -> FloorPlan:
        """
        Import a RoomPlan JSON file and create a FloorPlan.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            FloorPlan object populated with imported data
        """
        logger.info(f"Importing RoomPlan JSON from: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return self.import_from_dict(data, Path(filepath).stem)
    
    def import_from_dict(self, data: Dict[str, Any], name: str = "Imported Room") -> FloorPlan:
        """
        Convert RoomPlan JSON data to FloorPlan.
        
        Args:
            data: Parsed JSON dictionary
            name: Name for the floor plan
            
        Returns:
            FloorPlan object
        """
        # Extract room dimensions
        dims = data.get('dimensions', {})
        width = dims.get('width', 0) * self.scale_factor
        height = dims.get('height', 0) * self.scale_factor  # This is ceiling height
        length = dims.get('length', 0) * self.scale_factor
        
        logger.info(f"Room dimensions: {width:.1f}\" x {length:.1f}\" x {height:.1f}\" (W x L x H)")
        
        # Create floor plan
        floor_plan = FloorPlan(
            name=name,
            floor_level=0,
            elevation=0.0,
            ceiling_height=height
        )
        
        # Import walls (returns list of walls, not yet added to floor_plan)
        walls_data = data.get('walls', [])
        temp_walls = []
        if walls_data:
            logger.info(f"Importing {len(walls_data)} walls...")
            temp_walls = self._create_walls_from_data(walls_data)
            
            # Snap corners together
            logger.info("Snapping corners together...")
            snapped_count = self._snap_corners(temp_walls)
            logger.info(f"Snapped {snapped_count} corners within {self.corner_snap_tolerance}\"")
            
            # Reorder walls for proper sequence
            logger.info("Reordering walls into sequential loop...")
            ordered_walls = self._order_walls_fixed(temp_walls)
            
            # Add ordered walls to floor plan
            for wall in ordered_walls:
                floor_plan.add_wall(wall)
            
            logger.info(f"Added {len(ordered_walls)} walls in proper sequence")
        
        # Import doors
        doors_data = data.get('doors', [])
        if doors_data:
            logger.info(f"Importing {len(doors_data)} doors...")
            self._import_doors(floor_plan, doors_data)
        
        # Import windows
        windows_data = data.get('windows', [])
        if windows_data:
            logger.info(f"Importing {len(windows_data)} windows...")
            self._import_windows(floor_plan, windows_data)
        
        # Import objects (furniture and fixtures)
        objects_data = data.get('objects', [])
        if objects_data:
            logger.info(f"Importing {len(objects_data)} objects...")
            self._import_objects(floor_plan, objects_data)
        
        logger.info(f"Import complete: {floor_plan}")
        return floor_plan
    
    def _create_walls_from_data(self, walls_data: List[Dict]) -> List[Wall]:
        """Create Wall objects from JSON data (doesn't add to floor plan yet)."""
        
        walls = []
        
        for wall_data in walls_data:
            try:
                # Get wall dimensions (convert meters to inches)
                dims = wall_data.get('dimensions', {})
                wall_width = dims.get('width', 0) * self.scale_factor
                wall_height = dims.get('height', 0) * self.scale_factor
                wall_thickness = dims.get('thickness', 6.0)  # Default 6" if not specified
                
                # Get position
                transform = wall_data.get('transform', {})
                position = transform.get('position', {})
                pos_x = position.get('x', 0) * self.scale_factor
                pos_y = position.get('y', 0) * self.scale_factor
                pos_z = position.get('z', 0) * self.scale_factor
                
                # Extract rotation from matrix to determine wall orientation
                matrix = transform.get('matrix', None)
                if matrix and len(matrix) >= 4:
                    # RoomPlan matrix is in column-major order, but we treat it as row-major
                    # for extracting the direction vector
                    # Row 0 gives us the X-axis direction (wall extends along this)
                    # Elements [0] = X component, [2] = Z component (for 2D top-down view)
                    
                    right_x = matrix[0][0]  # Row 0, Column 0
                    right_z = matrix[0][2]  # Row 0, Column 2
                    
                    # Normalize the direction vector (in XZ plane for top-down view)
                    length = math.sqrt(right_x * right_x + right_z * right_z)
                    if length > 0.001:  # Avoid division by zero
                        dir_x = right_x / length
                        dir_z = right_z / length
                    else:
                        # Fallback to horizontal wall
                        dir_x = 1.0
                        dir_z = 0.0
                    
                    # Calculate start and end points along wall direction
                    half_width = wall_width / 2
                    
                    start = Point(
                        x=pos_x - dir_x * half_width,
                        y=pos_z - dir_z * half_width  # Note: RoomPlan Z becomes our Y (2D)
                    )
                    
                    end = Point(
                        x=pos_x + dir_x * half_width,
                        y=pos_z + dir_z * half_width
                    )
                else:
                    # Fallback: create horizontal wall
                    half_width = wall_width / 2
                    start = Point(x=pos_x - half_width, y=pos_z)
                    end = Point(x=pos_x + half_width, y=pos_z)
                
                # Determine if exterior or interior wall
                # Assume exterior if on room boundary (this is heuristic)
                wall_type = WallType.EXTERIOR  # RoomPlan typically captures exterior walls
                
                # Create wall
                wall = Wall(
                    start=start,
                    end=end,
                    thickness=wall_thickness if wall_thickness > 0 else 6.0,
                    wall_type=wall_type,
                    height=wall_height
                )
                
                walls.append(wall)
                logger.debug(f"Created wall: {wall.start} to {wall.end}, height={wall_height:.1f}\"")
                
            except Exception as e:
                logger.warning(f"Failed to import wall: {e}")
                continue
        
        return walls
    
    def _snap_corners(self, walls: List[Wall]) -> int:
        """
        Snap wall endpoints that are close together.
        
        Fixes the issue where RoomPlan walls don't share exact vertices,
        causing gaps in the floor plan even though corners appear connected.
        
        Args:
            walls: List of Wall objects
            
        Returns:
            Number of corners snapped
        """
        if not walls:
            return 0
        
        snapped_count = 0
        tolerance = self.corner_snap_tolerance
        
        # Collect all endpoints with their wall references
        endpoints: List[Tuple[Wall, bool]] = []  # (wall, is_start)
        for wall in walls:
            endpoints.append((wall, True))   # start point
            endpoints.append((wall, False))  # end point
        
        # Compare all pairs of endpoints
        for i in range(len(endpoints)):
            wall1, is_start1 = endpoints[i]
            point1 = wall1.start if is_start1 else wall1.end
            
            for j in range(i + 1, len(endpoints)):
                wall2, is_start2 = endpoints[j]
                point2 = wall2.start if is_start2 else wall2.end
                
                # Calculate distance
                distance = point1.distance_to(point2)
                
                # If close enough, snap to average position
                if distance > 0 and distance < tolerance:
                    # Calculate average position
                    avg_point = Point(
                        x=(point1.x + point2.x) / 2,
                        y=(point1.y + point2.y) / 2
                    )
                    
                    # Update both wall endpoints to use the same position
                    if is_start1:
                        wall1.start = avg_point
                    else:
                        wall1.end = avg_point
                    
                    if is_start2:
                        wall2.start = avg_point
                    else:
                        wall2.end = avg_point
                    
                    snapped_count += 1
                    logger.debug(f"Snapped corners: distance={distance:.2f}\" -> ({avg_point.x:.1f}, {avg_point.y:.1f})")
        
        return snapped_count
    
    def _order_walls_fixed(self, walls: List[Wall]) -> List[Wall]:
        """
        FIXED: Reorder walls into a sequential closed loop.
        
        This version properly traces wall connections by following the pattern:
        wall[i].end connects to wall[i+1].start
        
        Args:
            walls: List of Wall objects (with snapped corners)
            
        Returns:
            Ordered list of walls forming a connected sequential chain
        """
        if not walls:
            return []
        
        if len(walls) == 1:
            return walls
        
        logger.debug("Building wall connectivity graph...")
        
        # Build connectivity graph: for each wall, find which other walls connect to its endpoints
        graph = {}
        tolerance = 0.1  # Very small tolerance since corners are already snapped
        
        for i, wall in enumerate(walls):
            graph[i] = {'start_connects': [], 'end_connects': []}
            
            for j, other_wall in enumerate(walls):
                if i == j:
                    continue
                
                # Check if this wall's end connects to other wall's start
                if wall.end.distance_to(other_wall.start) < tolerance:
                    graph[i]['end_connects'].append(('start', j))
                
                # Check if this wall's end connects to other wall's end (would need flip)
                if wall.end.distance_to(other_wall.end) < tolerance:
                    graph[i]['end_connects'].append(('end', j))
                
                # Check if this wall's start connects to other wall's start
                if wall.start.distance_to(other_wall.start) < tolerance:
                    graph[i]['start_connects'].append(('start', j))
                
                # Check if this wall's start connects to other wall's end
                if wall.start.distance_to(other_wall.end) < tolerance:
                    graph[i]['start_connects'].append(('end', j))
        
        # Trace through the walls starting from wall 0
        logger.debug("Tracing wall sequence...")
        ordered = []
        visited = set()
        
        # Start with first wall
        current_idx = 0
        current_wall = walls[current_idx]
        ordered.append(current_wall)
        visited.add(current_idx)
        
        # Follow connections from current wall's end
        while len(visited) < len(walls):
            connections = graph[current_idx]['end_connects']
            
            # Find the next unvisited wall
            next_idx = None
            needs_flip = False
            
            for endpoint_type, wall_idx in connections:
                if wall_idx not in visited:
                    next_idx = wall_idx
                    needs_flip = (endpoint_type == 'end')  # If connecting end-to-end, need to flip
                    break
            
            if next_idx is None:
                logger.warning(f"Wall chain broken at wall {current_idx} - only found {len(visited)}/{len(walls)} walls")
                break
            
            # Get the next wall
            next_wall = walls[next_idx]
            
            # Flip if necessary so it starts where we ended
            if needs_flip:
                next_wall = Wall(
                    start=next_wall.end,
                    end=next_wall.start,
                    thickness=next_wall.thickness,
                    wall_type=next_wall.wall_type,
                    height=next_wall.height
                )
                logger.debug(f"Flipped wall {next_idx} for proper orientation")
            
            ordered.append(next_wall)
            visited.add(next_idx)
            current_idx = next_idx
        
        if len(ordered) != len(walls):
            logger.warning(f"Could not order all walls: {len(ordered)}/{len(walls)} in chain")
            logger.warning("Returning original order")
            return walls
        
        # Verify the loop closes
        first_wall = ordered[0]
        last_wall = ordered[-1]
        closing_distance = last_wall.end.distance_to(first_wall.start)
        
        if closing_distance < 1.0:
            logger.info(f"✓ Walls form a closed loop (closing gap: {closing_distance:.3f}\")")
        else:
            logger.warning(f"⚠ Walls do not close properly (gap: {closing_distance:.2f}\")")
        
        return ordered
    
    def _import_doors(self, floor_plan: FloorPlan, doors_data: List[Dict]):
        """Import door data and create Opening objects."""
        
        for door_data in doors_data:
            try:
                # Get dimensions
                dims = door_data.get('dimensions', {})
                door_width = dims.get('width', 36) * self.scale_factor  # Default 36" door
                door_height = dims.get('height', 80) * self.scale_factor  # Default 80" height
                
                # Get position
                transform = door_data.get('transform', {})
                position = transform.get('position', {})
                pos_x = position.get('x', 0) * self.scale_factor
                pos_z = position.get('z', 0) * self.scale_factor
                
                # Find nearest wall
                door_point = Point(x=pos_x, y=pos_z)
                nearest_wall = self._find_nearest_wall(floor_plan, door_point)
                
                if nearest_wall:
                    # Determine door type based on width
                    if door_width > 60:
                        door_type = OpeningType.DOOR_DOUBLE
                    else:
                        door_type = OpeningType.DOOR_SINGLE
                    
                    # Create opening on the nearest wall
                    opening = Opening(
                        wall_id=nearest_wall.id,
                        position=0.5,  # Middle of wall (will be adjusted)
                        width=door_width,
                        height=door_height,
                        opening_type=door_type
                    )
                    
                    # Adjust position based on actual location
                    opening.position = self._calculate_position_on_wall(
                        nearest_wall, door_point
                    )
                    
                    floor_plan.add_opening(opening)
                    logger.debug(f"Added door: width={door_width:.1f}\", height={door_height:.1f}\"")
                else:
                    logger.warning(f"Could not find wall for door at ({pos_x:.1f}, {pos_z:.1f})")
                    
            except Exception as e:
                logger.warning(f"Failed to import door: {e}")
                continue
    
    def _import_windows(self, floor_plan: FloorPlan, windows_data: List[Dict]):
        """Import window data and create Opening objects."""
        
        for window_data in windows_data:
            try:
                # Get dimensions
                dims = window_data.get('dimensions', {})
                window_width = dims.get('width', 36) * self.scale_factor
                window_height = dims.get('height', 48) * self.scale_factor
                
                # Get position
                transform = window_data.get('transform', {})
                position = transform.get('position', {})
                pos_x = position.get('x', 0) * self.scale_factor
                pos_z = position.get('z', 0) * self.scale_factor
                
                # Find nearest wall
                window_point = Point(x=pos_x, y=pos_z)
                nearest_wall = self._find_nearest_wall(floor_plan, window_point)
                
                if nearest_wall:
                    # Determine window type based on width
                    if window_width > 72:
                        window_type = OpeningType.WINDOW_PICTURE
                    elif window_width > 48:
                        window_type = OpeningType.WINDOW_DOUBLE
                    else:
                        window_type = OpeningType.WINDOW_SINGLE
                    
                    # Create opening
                    opening = Opening(
                        wall_id=nearest_wall.id,
                        position=0.5,
                        width=window_width,
                        height=window_height,
                        opening_type=window_type
                    )
                    
                    # Adjust position
                    opening.position = self._calculate_position_on_wall(
                        nearest_wall, window_point
                    )
                    
                    floor_plan.add_opening(opening)
                    logger.debug(f"Added window: width={window_width:.1f}\", height={window_height:.1f}\"")
                else:
                    logger.warning(f"Could not find wall for window at ({pos_x:.1f}, {pos_z:.1f})")
                    
            except Exception as e:
                logger.warning(f"Failed to import window: {e}")
                continue
    
    def _extract_rotation_from_matrix(self, transform: Dict) -> float:
        """
        Extract rotation angle in degrees from RoomPlan transform.
        
        Supports two formats:
        1. New format with explicit rotation field:
           "rotation": {"yaw_degrees": 90.0, "yaw_radians": 1.5708}
        2. Old format with transformation matrix (4x4 column-major)
        
        Returns rotation in degrees (0-360), where:
        - 0° = facing right (+X direction)
        - 90° = facing up (-Z direction in RoomPlan, +Y in our 2D space)
        - 180° = facing left (-X direction)
        - 270° = facing down (+Z direction in RoomPlan, -Y in our 2D space)
        """
        
        # First check for explicit rotation field (new format)
        rotation_data = transform.get('rotation', None)
        if rotation_data:
            # Try to get yaw_degrees directly
            yaw_degrees = rotation_data.get('yaw_degrees', None)
            if yaw_degrees is not None:
                # Normalize to 0-360 range
                angle = yaw_degrees % 360
                if angle < 0:
                    angle += 360
                logger.debug(f"Extracted rotation from yaw_degrees: {angle:.1f}°")
                return angle
            
            # Fallback to yaw_radians if degrees not available
            yaw_radians = rotation_data.get('yaw_radians', None)
            if yaw_radians is not None:
                angle_degrees = math.degrees(yaw_radians)
                # Normalize to 0-360 range
                angle = angle_degrees % 360
                if angle < 0:
                    angle += 360
                logger.debug(f"Extracted rotation from yaw_radians: {angle:.1f}°")
                return angle
        
        # Fallback to matrix extraction (old format)
        matrix = transform.get('matrix', None)
        
        if not matrix or len(matrix) < 1 or len(matrix[0]) < 3:
            return 0.0  # Default to 0° if no rotation data available
        
        try:
            # Extract the X-axis direction vector from the first row
            # matrix[0][0] = right direction X component
            # matrix[0][2] = right direction Z component (maps to Y in 2D)
            right_x = matrix[0][0]
            right_z = matrix[0][2]
            
            # Calculate angle using atan2
            # atan2(z, x) gives angle from +X axis in the XZ plane
            # We negate right_z because RoomPlan's +Z points forward (north),
            # but in our 2D coordinate system +Y points up (north)
            angle_radians = math.atan2(-right_z, right_x)
            
            # Convert to degrees
            angle_degrees = math.degrees(angle_radians)
            
            # Normalize to 0-360 range
            if angle_degrees < 0:
                angle_degrees += 360
            
            logger.debug(f"Extracted rotation from matrix: {angle_degrees:.1f}°")
            return angle_degrees
            
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Failed to extract rotation from matrix: {e}")
            return 0.0
    
    def _import_objects(self, floor_plan: FloorPlan, objects_data: List[Dict]):
        """Import furniture and fixture objects."""
        
        for obj_data in objects_data:
            try:
                category = obj_data.get('category', '').lower()
                
                # Get dimensions
                dims = obj_data.get('dimensions', {})
                width = dims.get('width', 24) * self.scale_factor
                height = dims.get('height', 30) * self.scale_factor
                depth = dims.get('depth', 24) * self.scale_factor
                
                # Get position and rotation
                transform = obj_data.get('transform', {})
                position = transform.get('position', {})
                pos_x = position.get('x', 0) * self.scale_factor
                pos_z = position.get('z', 0) * self.scale_factor
                
                pos = Point(x=pos_x, y=pos_z)
                
                # Extract rotation from transform matrix
                rotation_degrees = self._extract_rotation_from_matrix(transform)
                
                # Check if it's a fixture
                if category in self.FIXTURE_MAPPING:
                    fixture_type = self.FIXTURE_MAPPING[category]
                    
                    fixture = Fixture(
                        position=pos,
                        width=width,
                        depth=depth,
                        fixture_type=fixture_type,
                        rotation=rotation_degrees,
                        name=category.title()
                    )
                    
                    floor_plan.add_fixture(fixture)
                    logger.debug(f"Added fixture: {category} at ({pos_x:.1f}, {pos_z:.1f}), rotation: {rotation_degrees:.1f}°")
                    
                # Check if it's furniture
                elif category in self.FURNITURE_MAPPING:
                    furniture_type = self.FURNITURE_MAPPING[category]
                    
                    furniture = Furniture(
                        position=pos,
                        width=width,
                        depth=depth,
                        furniture_type=furniture_type,
                        rotation=rotation_degrees,
                        name=category.title()
                    )
                    
                    floor_plan.add_furniture(furniture)
                    logger.debug(f"Added furniture: {category} at ({pos_x:.1f}, {pos_z:.1f}), rotation: {rotation_degrees:.1f}°")
                else:
                    logger.debug(f"Unknown object category: {category}")
                    
            except Exception as e:
                logger.warning(f"Failed to import object: {e}")
                continue
    
    def _find_nearest_wall(self, floor_plan: FloorPlan, point: Point) -> Optional[Wall]:
        """Find the wall nearest to a given point."""
        if not floor_plan.walls:
            return None
        
        min_distance = float('inf')
        nearest_wall = None
        
        for wall in floor_plan.walls:
            # Calculate perpendicular distance to wall
            distance = self._point_to_wall_distance(point, wall)
            
            if distance < min_distance:
                min_distance = distance
                nearest_wall = wall
        
        return nearest_wall
    
    def _point_to_wall_distance(self, point: Point, wall: Wall) -> float:
        """Calculate perpendicular distance from point to wall."""
        # Vector from wall start to end
        wall_vec_x = wall.end.x - wall.start.x
        wall_vec_y = wall.end.y - wall.start.y
        wall_length_sq = wall_vec_x * wall_vec_x + wall_vec_y * wall_vec_y
        
        if wall_length_sq < 0.001:
            # Wall is essentially a point
            return point.distance_to(wall.start)
        
        # Vector from wall start to point
        point_vec_x = point.x - wall.start.x
        point_vec_y = point.y - wall.start.y
        
        # Project point onto wall line
        t = (point_vec_x * wall_vec_x + point_vec_y * wall_vec_y) / wall_length_sq
        t = max(0, min(1, t))  # Clamp to [0, 1]
        
        # Closest point on wall
        closest_x = wall.start.x + t * wall_vec_x
        closest_y = wall.start.y + t * wall_vec_y
        
        # Distance to closest point
        dx = point.x - closest_x
        dy = point.y - closest_y
        return math.sqrt(dx * dx + dy * dy)
    
    def _calculate_position_on_wall(self, wall: Wall, point: Point) -> float:
        """
        Calculate position along wall (0.0 to 1.0) where point projects.
        
        Args:
            wall: The wall
            point: The point to project
            
        Returns:
            Position from 0.0 (start) to 1.0 (end)
        """
        wall_vec_x = wall.end.x - wall.start.x
        wall_vec_y = wall.end.y - wall.start.y
        wall_length_sq = wall_vec_x * wall_vec_x + wall_vec_y * wall_vec_y
        
        if wall_length_sq < 0.001:
            return 0.5
        
        point_vec_x = point.x - wall.start.x
        point_vec_y = point.y - wall.start.y
        
        t = (point_vec_x * wall_vec_x + point_vec_y * wall_vec_y) / wall_length_sq
        return max(0.0, min(1.0, t))


def import_roomplan_json(filepath: str, corner_snap_tolerance: float = 6.0) -> FloorPlan:
    """
    Convenience function to import a RoomPlan JSON file.
    
    Args:
        filepath: Path to JSON file from iPhone RoomPlan scanner
        corner_snap_tolerance: Distance in inches within which to snap corners together (default: 6.0")
        
    Returns:
        FloorPlan object with imported data (corners snapped, walls ordered)
        
    Example:
        >>> floor_plan = import_roomplan_json("office.json")
        >>> print(f"Imported {len(floor_plan.walls)} walls")
    """
    importer = RoomPlanImporter(corner_snap_tolerance=corner_snap_tolerance)
    return importer.import_from_file(filepath)


def import_roomplan_to_building(filepath: str, building: Building, 
                                 floor_level: int = 0,
                                 corner_snap_tolerance: float = 6.0) -> FloorPlan:
    """
    Import RoomPlan JSON directly into a Building at a specific floor level.
    
    Args:
        filepath: Path to JSON file
        building: Building object to add floor to
        floor_level: Floor level number (0 = ground, 1 = first floor, etc.)
        corner_snap_tolerance: Distance in inches within which to snap corners together (default: 6.0")
        
    Returns:
        The created FloorPlan object
        
    Example:
        >>> building = Building(name="My House")
        >>> ground_floor = import_roomplan_to_building("living_room.json", building, 0)
        >>> first_floor = import_roomplan_to_building("bedroom.json", building, 1)
    """
    importer = RoomPlanImporter(corner_snap_tolerance=corner_snap_tolerance)
    floor_plan = importer.import_from_file(filepath)
    
    # Update floor level
    floor_plan.floor_level = floor_level
    floor_plan.elevation = floor_level * floor_plan.ceiling_height
    
    # Add to building
    building.add_floor(floor_plan)
    
    return floor_plan
