#!/usr/bin/env python3
"""
Example: Demonstrating New Features

This script shows how to use the new features added in version 1.1:
- Room creation and area calculation
- Measurement tools
- Property modification
- Statistics generation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import Point, Wall, WallType, Opening, OpeningType, Room, FloorPlan
from utils import (
    calculate_room_area, calculate_perimeter, get_floor_plan_statistics,
    format_statistics, MeasurementTool
)


def create_house_with_rooms():
    """Create a complete house with properly defined rooms."""
    plan = FloorPlan(name="House with Rooms")
    
    def ft(feet):
        return feet * 12
    
    print("Creating floor plan...")
    
    # Living room (20' x 15')
    w1 = Wall(Point(0, 0), Point(ft(20), 0), 6, WallType.EXTERIOR)
    w2 = Wall(Point(ft(20), 0), Point(ft(20), ft(15)), 6, WallType.EXTERIOR)
    w3 = Wall(Point(ft(20), ft(15)), Point(0, ft(15)), 6, WallType.EXTERIOR)
    w4 = Wall(Point(0, ft(15)), Point(0, 0), 6, WallType.EXTERIOR)
    
    plan.add_wall(w1)
    plan.add_wall(w2)
    plan.add_wall(w3)
    plan.add_wall(w4)
    
    # Create living room
    living_room = Room(
        name="Living Room",
        wall_ids=[w1.id, w2.id, w3.id, w4.id],
        color="#FFE4B5"
    )
    plan.add_room(living_room)
    
    # Kitchen (15' x 12')
    w5 = Wall(Point(ft(20), 0), Point(ft(35), 0), 6, WallType.EXTERIOR)
    w6 = Wall(Point(ft(35), 0), Point(ft(35), ft(12)), 6, WallType.EXTERIOR)
    w7 = Wall(Point(ft(35), ft(12)), Point(ft(20), ft(12)), 6, WallType.INTERIOR)
    # w2 is shared wall
    
    plan.add_wall(w5)
    plan.add_wall(w6)
    plan.add_wall(w7)
    
    # Create kitchen
    kitchen = Room(
        name="Kitchen",
        wall_ids=[w5.id, w6.id, w7.id, w2.id],
        color="#B0E0E6"
    )
    plan.add_room(kitchen)
    
    # Bedroom (12' x 10')
    w8 = Wall(Point(ft(20), ft(12)), Point(ft(20), ft(15)), 4, WallType.INTERIOR)
    w9 = Wall(Point(ft(20), ft(15)), Point(ft(32), ft(15)), 6, WallType.EXTERIOR)
    w10 = Wall(Point(ft(32), ft(15)), Point(ft(32), ft(12)), 6, WallType.EXTERIOR)
    # w7 shared with kitchen
    
    plan.add_wall(w8)
    plan.add_wall(w9)
    plan.add_wall(w10)
    
    # Create bedroom
    bedroom = Room(
        name="Bedroom",
        wall_ids=[w7.id, w8.id, w9.id, w10.id],
        color="#98FB98"
    )
    plan.add_room(bedroom)
    
    # Add doors and windows
    plan.add_opening(Opening(w1.id, 0.5, 36, OpeningType.DOOR))  # Front door
    plan.add_opening(Opening(w4.id, 0.5, 48, OpeningType.WINDOW, sill_height=36))  # Living room window
    plan.add_opening(Opening(w6.id, 0.5, 36, OpeningType.WINDOW, sill_height=36))  # Kitchen window
    plan.add_opening(Opening(w9.id, 0.5, 48, OpeningType.WINDOW, sill_height=36))  # Bedroom window
    plan.add_opening(Opening(w7.id, 0.8, 32, OpeningType.DOOR))  # Kitchen to bedroom door
    
    print(f"✓ Created {len(plan.walls)} walls")
    print(f"✓ Created {len(plan.rooms)} rooms")
    print(f"✓ Added {len(plan.openings)} openings")
    
    return plan


def demonstrate_room_calculations(plan):
    """Demonstrate room area and perimeter calculations."""
    print("\n" + "="*60)
    print("ROOM CALCULATIONS")
    print("="*60)
    
    for room in plan.rooms:
        area = calculate_room_area(room, plan)
        perimeter = calculate_perimeter(room, plan)
        
        print(f"\n{room.name}:")
        print(f"  Area: {area:.1f} sq ft")
        print(f"  Perimeter: {perimeter:.1f} ft")
        print(f"  Color: {room.color}")
        print(f"  Walls: {len(room.wall_ids)}")


def demonstrate_measurements():
    """Demonstrate measurement tool."""
    print("\n" + "="*60)
    print("MEASUREMENT TOOL EXAMPLE")
    print("="*60)
    
    tool = MeasurementTool()
    
    # Create some measurements
    tool.start_measurement(Point(0, 0))
    m1 = tool.finish_measurement(Point(144, 0), "Wall length")
    
    tool.start_measurement(Point(0, 0))
    m2 = tool.finish_measurement(Point(144, 144), "Diagonal")
    
    print(f"\nMeasurement 1 ({m1.label}):")
    print(f"  Distance: {m1.distance():.1f} inches ({m1.distance()/12:.1f} feet)")
    print(f"  Angle: {m1.angle():.1f}°")
    
    print(f"\nMeasurement 2 ({m2.label}):")
    print(f"  Distance: {m2.distance():.1f} inches ({m2.distance()/12:.1f} feet)")
    print(f"  Angle: {m2.angle():.1f}°")
    
    print(f"\nTotal measurements: {len(tool.measurements)}")


def demonstrate_statistics(plan):
    """Demonstrate comprehensive statistics."""
    print("\n" + "="*60)
    print("FLOOR PLAN STATISTICS")
    print("="*60)
    
    stats = get_floor_plan_statistics(plan)
    stats_text = format_statistics(stats)
    print("\n" + stats_text)


def demonstrate_property_modifications(plan):
    """Demonstrate modifying object properties."""
    print("\n" + "="*60)
    print("PROPERTY MODIFICATION EXAMPLE")
    print("="*60)
    
    # Get first wall
    wall = plan.walls[0]
    print(f"\nOriginal wall:")
    print(f"  Thickness: {wall.thickness}\"")
    print(f"  Type: {wall.wall_type.value}")
    print(f"  Length: {wall.length():.1f}\"")
    
    # Modify properties
    wall.thickness = 8.0
    wall.wall_type = WallType.LOAD_BEARING
    
    print(f"\nModified wall:")
    print(f"  Thickness: {wall.thickness}\"")
    print(f"  Type: {wall.wall_type.value}")
    print(f"  Length: {wall.length():.1f}\"")
    
    # Get first opening
    if plan.openings:
        opening = plan.openings[0]
        print(f"\nOriginal opening:")
        print(f"  Width: {opening.width}\"")
        print(f"  Height: {opening.height}\"")
        print(f"  Type: {opening.opening_type.value}")
        
        # Modify
        opening.width = 42.0
        opening.height = 84.0
        
        print(f"\nModified opening:")
        print(f"  Width: {opening.width}\"")
        print(f"  Height: {opening.height}\"")
        print(f"  Type: {opening.opening_type.value}")


def main():
    """Main demonstration."""
    print("="*60)
    print("FLOOR PLAN EDITOR - NEW FEATURES DEMONSTRATION")
    print("="*60)
    
    # Create house with rooms
    plan = create_house_with_rooms()
    
    # Demonstrate calculations
    demonstrate_room_calculations(plan)
    
    # Demonstrate measurements
    demonstrate_measurements()
    
    # Demonstrate statistics
    demonstrate_statistics(plan)
    
    # Demonstrate property modifications
    demonstrate_property_modifications(plan)
    
    # Save the plan
    output_dir = Path(__file__).parent
    output_file = output_dir / "house_with_features.floorplan"
    plan.save_to_file(str(output_file))
    
    print("\n" + "="*60)
    print(f"✓ Saved example to: {output_file}")
    print("  Open it in the GUI to see:")
    print("  - Rooms with colors and labels")
    print("  - Property panel for editing")
    print("  - Statistics in Analysis menu")
    print("  - Measurement tool (M key)")
    print(f"\nCommand: python main.py {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()

