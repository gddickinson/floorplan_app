"""
RoomPlan JSON Importer for Floor Plan Editor

Imports 3D room scans from iPhone LiDAR/RoomPlan into 2D floor plans.
Converts meters to inches, extracts 2D footprint from 3D data.
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
    
    def __init__(self):
        self.scale_factor = self.METERS_TO_INCHES
    
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
        
        # Import walls
        walls_data = data.get('walls', [])
        if walls_data:
            logger.info(f"Importing {len(walls_data)} walls...")
            self._import_walls(floor_plan, walls_data)
        
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
    
    def _import_walls(self, floor_plan: FloorPlan, walls_data: List[Dict]):
        """Import wall data and create Wall objects."""
        
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
                    # Matrix is 4x4 transform matrix (column-major order)
                    # Column 0 (right vector) = direction along wall width
                    # Column 1 (up vector) = vertical direction  
                    # Column 2 (forward vector) = normal to wall surface
                    # Column 3 = position
                    
                    # For walls, width dimension extends along the "right" vector (column 0)
                    # Extract direction along wall from first column
                    right_x = matrix[0][0]  # m00 - right vector X component
                    right_z = matrix[2][0]  # m20 - right vector Z component
                    
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
                
                floor_plan.add_wall(wall)
                logger.debug(f"Added wall: {wall.start} to {wall.end}, height={wall_height:.1f}\"")
                
            except Exception as e:
                logger.warning(f"Failed to import wall: {e}")
                continue
    
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
                
                # Get position
                transform = obj_data.get('transform', {})
                position = transform.get('position', {})
                pos_x = position.get('x', 0) * self.scale_factor
                pos_z = position.get('z', 0) * self.scale_factor
                
                pos = Point(x=pos_x, y=pos_z)
                
                # Check if it's a fixture
                if category in self.FIXTURE_MAPPING:
                    fixture_type = self.FIXTURE_MAPPING[category]
                    
                    fixture = Fixture(
                        position=pos,
                        width=width,
                        depth=depth,
                        fixture_type=fixture_type,
                        rotation=0,
                        name=category.title()
                    )
                    
                    floor_plan.add_fixture(fixture)
                    logger.debug(f"Added fixture: {category} at ({pos_x:.1f}, {pos_z:.1f})")
                    
                # Check if it's furniture
                elif category in self.FURNITURE_MAPPING:
                    furniture_type = self.FURNITURE_MAPPING[category]
                    
                    furniture = Furniture(
                        position=pos,
                        width=width,
                        depth=depth,
                        furniture_type=furniture_type,
                        rotation=0,
                        name=category.title()
                    )
                    
                    floor_plan.add_furniture(furniture)
                    logger.debug(f"Added furniture: {category} at ({pos_x:.1f}, {pos_z:.1f})")
                else:
                    logger.debug(f"Skipping unknown object category: {category}")
                    
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
            distance = self._point_to_line_distance(point, wall.start, wall.end)
            if distance < min_distance:
                min_distance = distance
                nearest_wall = wall
        
        return nearest_wall
    
    def _point_to_line_distance(self, point: Point, line_start: Point, line_end: Point) -> float:
        """Calculate perpendicular distance from point to line segment."""
        # Vector from line_start to line_end
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y
        
        if dx == 0 and dy == 0:
            # Line is a point
            return point.distance_to(line_start)
        
        # Parameter t represents position along line (0 to 1 for segment)
        t = ((point.x - line_start.x) * dx + (point.y - line_start.y) * dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))  # Clamp to segment
        
        # Nearest point on segment
        nearest_x = line_start.x + t * dx
        nearest_y = line_start.y + t * dy
        nearest = Point(x=nearest_x, y=nearest_y)
        
        return point.distance_to(nearest)
    
    def _calculate_position_on_wall(self, wall: Wall, point: Point) -> float:
        """
        Calculate normalized position (0-1) of a point along a wall.
        
        Args:
            wall: Wall object
            point: Point near the wall
            
        Returns:
            Position from 0 (start) to 1 (end)
        """
        # Vector from wall start to end
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        wall_length_sq = dx*dx + dy*dy
        
        if wall_length_sq == 0:
            return 0.5
        
        # Project point onto wall line
        t = ((point.x - wall.start.x) * dx + (point.y - wall.start.y) * dy) / wall_length_sq
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, t))


def import_roomplan_json(filepath: str) -> FloorPlan:
    """
    Convenience function to import a RoomPlan JSON file.
    
    Args:
        filepath: Path to JSON file from iPhone RoomPlan scanner
        
    Returns:
        FloorPlan object with imported data
        
    Example:
        >>> floor_plan = import_roomplan_json("office.json")
        >>> print(f"Imported {len(floor_plan.walls)} walls")
    """
    importer = RoomPlanImporter()
    return importer.import_from_file(filepath)


def import_roomplan_to_building(filepath: str, building: Building, 
                                 floor_level: int = 0) -> FloorPlan:
    """
    Import RoomPlan JSON directly into a Building at a specific floor level.
    
    Args:
        filepath: Path to JSON file
        building: Building object to add floor to
        floor_level: Floor level number (0 = ground, 1 = first floor, etc.)
        
    Returns:
        The created FloorPlan object
        
    Example:
        >>> building = Building(name="My House")
        >>> ground_floor = import_roomplan_to_building("living_room.json", building, 0)
        >>> first_floor = import_roomplan_to_building("bedroom.json", building, 1)
    """
    importer = RoomPlanImporter()
    floor_plan = importer.import_from_file(filepath)
    
    # Update floor level
    floor_plan.floor_level = floor_level
    floor_plan.elevation = floor_level * floor_plan.ceiling_height
    
    # Add to building
    building.add_floor(floor_plan)
    
    return floor_plan
