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
from core.plan_stats import (  # noqa: F401  (re-exported)
    calculate_room_area, calculate_polygon_area, calculate_perimeter,
    calculate_total_wall_length, calculate_total_area,
    get_floor_plan_statistics, format_statistics,
)

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

