"""
Floor plan statistics: room areas and perimeters, wall lengths, opening counts (no GUI dependencies).

Moved from utils/measurements.py (which re-exports these names) so the web API and editor share them.
Areas are in square feet, lengths in feet; the model unit is the inch.
"""

import logging
from typing import List, Optional

from .geometry import Point, Room, FloorPlan
from .room_geometry import room_polygon

logger = logging.getLogger(__name__)


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
    
    # Outline from the walls joined in walking order (the listed order is the click order)
    unique_points = room_polygon(room, floor_plan)
    if len(unique_points) < 3:
        logger.warning(f"Room {room.name} has insufficient points for area calculation")
        return None

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
            'doors': sum(1 for o in floor_plan.openings if o.opening_type.is_door),
            'windows': sum(1 for o in floor_plan.openings if o.opening_type.is_window),
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
