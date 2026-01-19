"""
iPhone LiDAR Scan Importer

Imports room scan data from iPhone RoomPlan JSON format and converts
to Floor Plan Editor format.
"""

import json
import math
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from core import (
    Point, Wall, Opening, OpeningType, Room, Furniture, FurnitureType,
    Fixture, FixtureType, FloorPlan, WallType, WallStyle
)

import logging

logger = logging.getLogger(__name__)


class iPhoneScanImporter:
    """
    Import room scans from iPhone LiDAR (RoomPlan) JSON format.
    
    Converts 3D room data to 2D floor plan:
    - Meters to inches
    - 3D coordinates (x, y, z) to 2D (x, z) where y is height
    - Wall transforms to start/end points
    - Objects to furniture/fixtures
    """
    
    METERS_TO_INCHES = 39.3701  # 1 meter = 39.3701 inches
    
    def __init__(self):
        self.floor_plan: Optional[FloorPlan] = None
        self.wall_map: Dict[str, Wall] = {}  # Map wall IDs to Wall objects
    
    def import_from_file(self, filepath: str) -> FloorPlan:
        """
        Import a floor plan from iPhone scan JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            FloorPlan object with imported data
        """
        logger.info(f"Importing iPhone scan from: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return self.import_from_dict(data, Path(filepath).stem)
    
    def import_from_dict(self, data: Dict[str, Any], name: str = "Imported Scan") -> FloorPlan:
        """
        Import floor plan from parsed JSON data.
        
        Args:
            data: Parsed JSON dictionary
            name: Name for the floor plan
            
        Returns:
            FloorPlan object
        """
        # Create floor plan
        self.floor_plan = FloorPlan(name=name)
        
        # Get dimensions (optional, for reference)
        dimensions = data.get("dimensions", {})
        logger.info(f"Room dimensions: {dimensions}")
        
        # Import walls first (needed for placing openings)
        walls_data = data.get("walls", [])
        logger.info(f"Importing {len(walls_data)} walls...")
        for wall_data in walls_data:
            self._import_wall(wall_data)
        
        # Import doors
        doors_data = data.get("doors", [])
        logger.info(f"Importing {len(doors_data)} doors...")
        for door_data in doors_data:
            self._import_door(door_data)
        
        # Import windows
        windows_data = data.get("windows", [])
        logger.info(f"Importing {len(windows_data)} windows...")
        for window_data in windows_data:
            self._import_window(window_data)
        
        # Import objects (furniture/fixtures)
        objects_data = data.get("objects", [])
        logger.info(f"Importing {len(objects_data)} objects...")
        for object_data in objects_data:
            self._import_object(object_data)
        
        logger.info(f"Import complete: {self.floor_plan}")
        return self.floor_plan
    
    def _import_wall(self, wall_data: Dict[str, Any]):
        """Import a wall from JSON data."""
        wall_id = wall_data.get("id")
        dimensions = wall_data.get("dimensions", {})
        transform = wall_data.get("transform", {})
        
        # Get wall dimensions in inches
        width = dimensions.get("width", 0) * self.METERS_TO_INCHES
        height = dimensions.get("height", 0) * self.METERS_TO_INCHES
        thickness = dimensions.get("thickness", 6)  # Default 6" if not specified
        
        # Get position
        position = transform.get("position", {})
        pos_x = position.get("x", 0) * self.METERS_TO_INCHES
        pos_y = position.get("y", 0) * self.METERS_TO_INCHES  # This is height (vertical)
        pos_z = position.get("z", 0) * self.METERS_TO_INCHES
        
        # Get rotation from transform matrix
        matrix = transform.get("matrix", [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
        
        # Extract rotation angle around Y axis (vertical)
        # The wall orientation is in the XZ plane
        # matrix[0][0] and matrix[0][2] give us the X axis direction
        # matrix[2][0] and matrix[2][2] give us the Z axis direction
        angle = math.atan2(matrix[0][2], matrix[0][0])
        
        # Calculate wall endpoints in 2D (x, z plane - top-down view)
        # The wall extends perpendicular to its facing direction
        half_width = width / 2
        
        # Direction perpendicular to wall normal
        perp_x = math.cos(angle)
        perp_z = math.sin(angle)
        
        # Calculate start and end points
        start_x = pos_x - perp_x * half_width
        start_z = pos_z - perp_z * half_width
        end_x = pos_x + perp_x * half_width
        end_z = pos_z + perp_z * half_width
        
        # Create wall (using z as y coordinate for top-down view)
        start = Point(start_x, start_z)
        end = Point(end_x, end_z)
        
        wall = Wall(
            start=start,
            end=end,
            thickness=thickness,
            wall_type=WallType.EXTERIOR,  # Assume exterior, can be refined
            wall_style=WallStyle.SOLID,
            height=height
        )
        
        self.floor_plan.add_wall(wall)
        self.wall_map[wall_id] = wall
        
        logger.debug(f"Imported wall {wall_id}: ({start_x:.1f}, {start_z:.1f}) to ({end_x:.1f}, {end_z:.1f})")
    
    def _import_door(self, door_data: Dict[str, Any]):
        """Import a door from JSON data."""
        door_id = door_data.get("id")
        dimensions = door_data.get("dimensions", {})
        transform = door_data.get("transform", {})
        
        # Get dimensions in inches
        width = dimensions.get("width", 36) * self.METERS_TO_INCHES
        height = dimensions.get("height", 80) * self.METERS_TO_INCHES
        
        # Get position (2D: use x and z)
        position = transform.get("position", {})
        pos_x = position.get("x", 0) * self.METERS_TO_INCHES
        pos_z = position.get("z", 0) * self.METERS_TO_INCHES
        
        # Find nearest wall
        door_point = Point(pos_x, pos_z)
        nearest_wall = self._find_nearest_wall(door_point)
        
        if nearest_wall:
            # Calculate position along wall
            wall_position = self._point_position_on_wall(door_point, nearest_wall)
            
            opening = Opening(
                wall_id=nearest_wall.id,
                position=wall_position,
                width=width,
                height=height,
                opening_type=OpeningType.DOOR_SINGLE  # Default to single door
            )
            
            self.floor_plan.add_opening(opening)
            logger.debug(f"Imported door {door_id} on wall {nearest_wall.id}")
        else:
            logger.warning(f"Could not find wall for door {door_id}")
    
    def _import_window(self, window_data: Dict[str, Any]):
        """Import a window from JSON data."""
        window_id = window_data.get("id")
        dimensions = window_data.get("dimensions", {})
        transform = window_data.get("transform", {})
        
        # Get dimensions in inches
        width = dimensions.get("width", 36) * self.METERS_TO_INCHES
        height = dimensions.get("height", 48) * self.METERS_TO_INCHES
        
        # Get position
        position = transform.get("position", {})
        pos_x = position.get("x", 0) * self.METERS_TO_INCHES
        pos_z = position.get("z", 0) * self.METERS_TO_INCHES
        
        # Find nearest wall
        window_point = Point(pos_x, pos_z)
        nearest_wall = self._find_nearest_wall(window_point)
        
        if nearest_wall:
            # Calculate position along wall
            wall_position = self._point_position_on_wall(window_point, nearest_wall)
            
            opening = Opening(
                wall_id=nearest_wall.id,
                position=wall_position,
                width=width,
                height=height,
                opening_type=OpeningType.WINDOW_SINGLE  # Default to single window
            )
            
            self.floor_plan.add_opening(opening)
            logger.debug(f"Imported window {window_id} on wall {nearest_wall.id}")
        else:
            logger.warning(f"Could not find wall for window {window_id}")
    
    def _import_object(self, object_data: Dict[str, Any]):
        """Import an object (furniture or fixture) from JSON data."""
        object_id = object_data.get("id")
        category = object_data.get("category", "").lower()
        dimensions = object_data.get("dimensions", {})
        transform = object_data.get("transform", {})
        confidence = object_data.get("confidence", "medium")
        
        # Get dimensions in inches
        width = dimensions.get("width", 24) * self.METERS_TO_INCHES
        height = dimensions.get("height", 30) * self.METERS_TO_INCHES
        depth = dimensions.get("depth", 24) * self.METERS_TO_INCHES
        
        # Get position (2D)
        position = transform.get("position", {})
        pos_x = position.get("x", 0) * self.METERS_TO_INCHES
        pos_z = position.get("z", 0) * self.METERS_TO_INCHES
        
        obj_position = Point(pos_x, pos_z)
        
        # Determine if it's furniture or fixture based on category
        if self._is_fixture_category(category):
            # Create fixture
            fixture_type = self._map_to_fixture_type(category)
            
            fixture = Fixture(
                position=obj_position,
                width=width,
                depth=depth,
                fixture_type=fixture_type,
                rotation=0  # Could extract from transform matrix if needed
            )
            
            self.floor_plan.add_fixture(fixture)
            logger.debug(f"Imported fixture {object_id}: {category} -> {fixture_type}")
            
        else:
            # Create furniture
            furniture_type = self._map_to_furniture_type(category)
            
            furniture = Furniture(
                position=obj_position,
                width=width,
                depth=depth,
                furniture_type=furniture_type,
                rotation=0  # Could extract from transform matrix if needed
            )
            
            self.floor_plan.add_furniture(furniture)
            logger.debug(f"Imported furniture {object_id}: {category} -> {furniture_type}")
    
    def _find_nearest_wall(self, point: Point) -> Optional[Wall]:
        """Find the wall nearest to a given point."""
        if not self.floor_plan.walls:
            return None
        
        min_distance = float('inf')
        nearest_wall = None
        
        for wall in self.floor_plan.walls:
            distance = self._point_to_wall_distance(point, wall)
            if distance < min_distance:
                min_distance = distance
                nearest_wall = wall
        
        return nearest_wall
    
    def _point_to_wall_distance(self, point: Point, wall: Wall) -> float:
        """Calculate perpendicular distance from point to wall."""
        # Vector from wall start to point
        px = point.x - wall.start.x
        py = point.y - wall.start.y
        
        # Wall vector
        wx = wall.end.x - wall.start.x
        wy = wall.end.y - wall.start.y
        
        # Wall length squared
        wall_len_sq = wx * wx + wy * wy
        
        if wall_len_sq == 0:
            # Wall is a point
            return math.sqrt(px * px + py * py)
        
        # Project point onto wall line
        t = max(0, min(1, (px * wx + py * wy) / wall_len_sq))
        
        # Closest point on wall
        closest_x = wall.start.x + t * wx
        closest_y = wall.start.y + t * wy
        
        # Distance to closest point
        dx = point.x - closest_x
        dy = point.y - closest_y
        
        return math.sqrt(dx * dx + dy * dy)
    
    def _point_position_on_wall(self, point: Point, wall: Wall) -> float:
        """Calculate position along wall (0.0 = start, 1.0 = end)."""
        # Vector from wall start to point
        px = point.x - wall.start.x
        py = point.y - wall.start.y
        
        # Wall vector
        wx = wall.end.x - wall.start.x
        wy = wall.end.y - wall.start.y
        
        # Wall length squared
        wall_len_sq = wx * wx + wy * wy
        
        if wall_len_sq == 0:
            return 0.5  # Wall is a point, use middle
        
        # Project point onto wall line
        t = (px * wx + py * wy) / wall_len_sq
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, t))
    
    def _is_fixture_category(self, category: str) -> bool:
        """Determine if a category should be a fixture vs furniture."""
        fixture_categories = {
            'toilet', 'sink', 'bathtub', 'shower', 
            'refrigerator', 'stove', 'oven', 'dishwasher',
            'washer', 'dryer', 'fireplace'
        }
        return category in fixture_categories
    
    def _map_to_fixture_type(self, category: str) -> FixtureType:
        """Map iPhone category to FixtureType."""
        mapping = {
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
        return mapping.get(category, FixtureType.SINK)  # Default to sink
    
    def _map_to_furniture_type(self, category: str) -> FurnitureType:
        """Map iPhone category to FurnitureType."""
        mapping = {
            'bed': FurnitureType.BED_QUEEN,  # Default to queen
            'chair': FurnitureType.CHAIR,
            'sofa': FurnitureType.SOFA,
            'table': FurnitureType.TABLE_DINING,
            'storage': FurnitureType.CABINET,
            'desk': FurnitureType.DESK,
        }
        return mapping.get(category, FurnitureType.TABLE_COFFEE)  # Default to coffee table


def import_iphone_scan(filepath: str) -> FloorPlan:
    """
    Convenience function to import an iPhone scan.
    
    Args:
        filepath: Path to the JSON scan file
        
    Returns:
        FloorPlan object
    """
    importer = iPhoneScanImporter()
    return importer.import_from_file(filepath)
