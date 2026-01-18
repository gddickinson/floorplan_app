"""
Measurement and calculation utilities for floor plans.

Provides tools for measuring distances, calculating areas,
and analyzing floor plan geometry.
"""

import logging
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass

from core import Point, Wall, Room, FloorPlan

logger = logging.getLogger(__name__)


@dataclass
class Measurement:
    """Container for a measurement."""
    start: Point
    end: Point
    label: str = ""
    
    def distance(self) -> float:
        """Get the distance in inches."""
        return self.start.distance_to(self.end)
    
    def angle(self) -> float:
        """Get the angle in degrees (0-360)."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        return (angle_deg + 360) % 360


def calculate_room_area(room: Room, floor_plan: FloorPlan) -> Optional[float]:
    """
    Calculate the area of a room in square feet.
    
    Uses the shoelace formula to calculate polygon area from wall vertices.
    
    Args:
        room: Room to calculate area for
        floor_plan: Floor plan containing the walls
        
    Returns:
        Area in square feet, or None if calculation fails
    """
    if not room.wall_ids:
        logger.warning(f"Room {room.name} has no walls")
        return None
    
    # Get all wall endpoints
    points = []
    for wall_id in room.wall_ids:
        wall = floor_plan.get_wall(wall_id)
        if wall:
            points.append(wall.start)
            points.append(wall.end)
    
    if len(points) < 3:
        logger.warning(f"Room {room.name} has insufficient points for area calculation")
        return None
    
    # Remove duplicates while preserving order
    unique_points = []
    seen = set()
    for p in points:
        key = (round(p.x, 2), round(p.y, 2))
        if key not in seen:
            unique_points.append(p)
            seen.add(key)
    
    # Calculate area using shoelace formula
    area_sq_inches = calculate_polygon_area(unique_points)
    area_sq_feet = area_sq_inches / 144.0  # Convert to square feet
    
    logger.info(f"Calculated area for room {room.name}: {area_sq_feet:.2f} sq ft")
    return area_sq_feet


def calculate_polygon_area(points: List[Point]) -> float:
    """
    Calculate area of a polygon using the shoelace formula.
    
    Args:
        points: List of points forming the polygon
        
    Returns:
        Area in square inches
    """
    if len(points) < 3:
        return 0.0
    
    # Shoelace formula
    area = 0.0
    n = len(points)
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
    
    return abs(area) / 2.0


def calculate_perimeter(room: Room, floor_plan: FloorPlan) -> float:
    """
    Calculate the perimeter of a room in feet.
    
    Args:
        room: Room to calculate perimeter for
        floor_plan: Floor plan containing the walls
        
    Returns:
        Perimeter in feet
    """
    total_length = 0.0
    
    for wall_id in room.wall_ids:
        wall = floor_plan.get_wall(wall_id)
        if wall:
            total_length += wall.length()
    
    return total_length / 12.0  # Convert to feet


def find_nearest_wall(point: Point, floor_plan: FloorPlan, 
                      max_distance: float = 50.0) -> Optional[Tuple[Wall, float]]:
    """
    Find the nearest wall to a given point.
    
    Args:
        point: Point to search from
        floor_plan: Floor plan to search in
        max_distance: Maximum search distance in inches
        
    Returns:
        Tuple of (wall, distance) or None if no wall found
    """
    nearest_wall = None
    nearest_distance = max_distance
    
    for wall in floor_plan.walls:
        distance = point_to_line_distance(point, wall.start, wall.end)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_wall = wall
    
    if nearest_wall:
        return (nearest_wall, nearest_distance)
    return None


def point_to_line_distance(point: Point, line_start: Point, line_end: Point) -> float:
    """
    Calculate perpendicular distance from point to line segment.
    
    Args:
        point: Point to measure from
        line_start: Start of line segment
        line_end: End of line segment
        
    Returns:
        Distance in inches
    """
    # Vector from line_start to line_end
    dx = line_end.x - line_start.x
    dy = line_end.y - line_start.y
    
    line_length_sq = dx * dx + dy * dy
    
    if line_length_sq < 0.01:  # Line is essentially a point
        return point.distance_to(line_start)
    
    # Calculate projection of point onto line
    t = max(0, min(1, (
        (point.x - line_start.x) * dx + (point.y - line_start.y) * dy
    ) / line_length_sq))
    
    # Find nearest point on line segment
    nearest_x = line_start.x + t * dx
    nearest_y = line_start.y + t * dy
    nearest_point = Point(nearest_x, nearest_y)
    
    return point.distance_to(nearest_point)


def calculate_total_wall_length(floor_plan: FloorPlan, wall_type: Optional[str] = None) -> float:
    """
    Calculate total length of walls in the floor plan.
    
    Args:
        floor_plan: Floor plan to analyze
        wall_type: Optional filter by wall type
        
    Returns:
        Total length in feet
    """
    total = 0.0
    
    for wall in floor_plan.walls:
        if wall_type is None or wall.wall_type.value == wall_type:
            total += wall.length()
    
    return total / 12.0  # Convert to feet


def calculate_total_area(floor_plan: FloorPlan) -> float:
    """
    Calculate total area of all rooms in the floor plan.
    
    Args:
        floor_plan: Floor plan to analyze
        
    Returns:
        Total area in square feet
    """
    total = 0.0
    
    for room in floor_plan.rooms:
        area = calculate_room_area(room, floor_plan)
        if area:
            total += area
    
    return total


def get_floor_plan_statistics(floor_plan: FloorPlan) -> dict:
    """
    Get comprehensive statistics about a floor plan.
    
    Args:
        floor_plan: Floor plan to analyze
        
    Returns:
        Dictionary of statistics
    """
    stats = {
        'walls': {
            'count': len(floor_plan.walls),
            'total_length_ft': calculate_total_wall_length(floor_plan),
            'exterior_length_ft': calculate_total_wall_length(floor_plan, 'exterior'),
            'interior_length_ft': calculate_total_wall_length(floor_plan, 'interior'),
        },
        'openings': {
            'count': len(floor_plan.openings),
            'doors': sum(1 for o in floor_plan.openings if o.opening_type.value == 'door'),
            'windows': sum(1 for o in floor_plan.openings if o.opening_type.value == 'window'),
            'archways': sum(1 for o in floor_plan.openings if o.opening_type.value == 'archway'),
        },
        'rooms': {
            'count': len(floor_plan.rooms),
            'total_area_sqft': calculate_total_area(floor_plan),
        }
    }
    
    # Add individual room areas
    stats['rooms']['individual'] = {}
    for room in floor_plan.rooms:
        area = calculate_room_area(room, floor_plan)
        if area:
            stats['rooms']['individual'][room.name] = {
                'area_sqft': area,
                'perimeter_ft': calculate_perimeter(room, floor_plan)
            }
    
    # Calculate bounds
    bounds = floor_plan.get_bounds()
    if bounds:
        min_pt, max_pt = bounds
        width_ft = (max_pt.x - min_pt.x) / 12.0
        height_ft = (max_pt.y - min_pt.y) / 12.0
        stats['dimensions'] = {
            'width_ft': width_ft,
            'height_ft': height_ft,
            'bounding_box_area_sqft': width_ft * height_ft
        }
    
    logger.info(f"Generated statistics for {floor_plan.name}")
    return stats


def format_statistics(stats: dict) -> str:
    """
    Format statistics dictionary as readable text.
    
    Args:
        stats: Statistics dictionary from get_floor_plan_statistics
        
    Returns:
        Formatted string
    """
    lines = []
    
    # Walls
    lines.append("=== Walls ===")
    lines.append(f"Total: {stats['walls']['count']}")
    lines.append(f"Total Length: {stats['walls']['total_length_ft']:.1f} ft")
    if stats['walls']['exterior_length_ft'] > 0:
        lines.append(f"  Exterior: {stats['walls']['exterior_length_ft']:.1f} ft")
    if stats['walls']['interior_length_ft'] > 0:
        lines.append(f"  Interior: {stats['walls']['interior_length_ft']:.1f} ft")
    
    # Openings
    lines.append("\n=== Openings ===")
    lines.append(f"Total: {stats['openings']['count']}")
    lines.append(f"  Doors: {stats['openings']['doors']}")
    lines.append(f"  Windows: {stats['openings']['windows']}")
    if stats['openings']['archways'] > 0:
        lines.append(f"  Archways: {stats['openings']['archways']}")
    
    # Rooms
    lines.append("\n=== Rooms ===")
    lines.append(f"Total: {stats['rooms']['count']}")
    lines.append(f"Total Area: {stats['rooms']['total_area_sqft']:.1f} sq ft")
    
    if stats['rooms']['individual']:
        lines.append("\nIndividual Rooms:")
        for name, data in stats['rooms']['individual'].items():
            lines.append(f"  {name}:")
            lines.append(f"    Area: {data['area_sqft']:.1f} sq ft")
            lines.append(f"    Perimeter: {data['perimeter_ft']:.1f} ft")
    
    # Dimensions
    if 'dimensions' in stats:
        lines.append("\n=== Dimensions ===")
        lines.append(f"Width: {stats['dimensions']['width_ft']:.1f} ft")
        lines.append(f"Height: {stats['dimensions']['height_ft']:.1f} ft")
        lines.append(f"Bounding Box: {stats['dimensions']['bounding_box_area_sqft']:.1f} sq ft")
    
    return "\n".join(lines)


class MeasurementTool:
    """
    Tool for measuring distances in a floor plan.
    
    Maintains a list of measurements for display.
    """
    
    def __init__(self):
        self.measurements: List[Measurement] = []
        self.temp_start: Optional[Point] = None
        
        logger.info("MeasurementTool initialized")
    
    def start_measurement(self, point: Point):
        """Start a new measurement from a point."""
        self.temp_start = point
        logger.debug(f"Started measurement at {point}")
    
    def finish_measurement(self, point: Point, label: str = ""):
        """Finish the measurement and add to list."""
        if self.temp_start:
            measurement = Measurement(self.temp_start, point, label)
            self.measurements.append(measurement)
            logger.info(f"Added measurement: {measurement.distance():.1f}\" at {measurement.angle():.1f}°")
            self.temp_start = None
            return measurement
        return None
    
    def cancel_measurement(self):
        """Cancel the current measurement."""
        self.temp_start = None
    
    def clear_measurements(self):
        """Clear all measurements."""
        self.measurements.clear()
        logger.info("Cleared all measurements")
    
    def get_temp_measurement(self, current_point: Point) -> Optional[Measurement]:
        """Get temporary measurement for preview."""
        if self.temp_start:
            return Measurement(self.temp_start, current_point, "temp")
        return None
