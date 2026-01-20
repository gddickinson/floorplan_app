#!/usr/bin/env python3
"""
Example: Creating a Simple House Floor Plan Programmatically

This script demonstrates how to create a floor plan using the core
geometry classes without the GUI. Useful for:
- Batch generation of floor plans
- Testing and validation
- Integration with other tools
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import Point, Wall, WallType, Opening, OpeningType, Room, FloorPlan


def create_simple_house():
    """
    Create a simple rectangular house with two rooms.
    
    Layout:
    - Living room: 20' x 15'
    - Bedroom: 12' x 12'
    - Hallway connecting them
    """
    
    # Create floor plan
    plan = FloorPlan(name="Simple House Example")
    
    # Convert feet to inches for measurements
    def ft(feet):
        return feet * 12
    
    # Living room (left side)
    # Bottom wall
    w1 = Wall(
        start=Point(0, 0),
        end=Point(ft(20), 0),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w1)
    
    # Right wall (partial - for hallway)
    w2 = Wall(
        start=Point(ft(20), 0),
        end=Point(ft(20), ft(15)),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w2)
    
    # Top wall
    w3 = Wall(
        start=Point(ft(20), ft(15)),
        end=Point(0, ft(15)),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w3)
    
    # Left wall
    w4 = Wall(
        start=Point(0, ft(15)),
        end=Point(0, 0),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w4)
    
    # Bedroom (right side)
    # Bottom wall (continuing from living room)
    w5 = Wall(
        start=Point(ft(20), 0),
        end=Point(ft(32), 0),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w5)
    
    # Right wall
    w6 = Wall(
        start=Point(ft(32), 0),
        end=Point(ft(32), ft(12)),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w6)
    
    # Top wall (bedroom)
    w7 = Wall(
        start=Point(ft(32), ft(12)),
        end=Point(ft(20), ft(12)),
        thickness=6,
        wall_type=WallType.EXTERIOR
    )
    plan.add_wall(w7)
    
    # Interior wall separating bedroom from living room
    w8 = Wall(
        start=Point(ft(20), ft(12)),
        end=Point(ft(20), ft(15)),
        thickness=4,
        wall_type=WallType.INTERIOR
    )
    plan.add_wall(w8)
    
    # Add front door to living room (bottom wall, centered)
    front_door = Opening(
        wall_id=w1.id,
        position=0.5,  # Center of wall
        width=36,  # 3 feet
        opening_type=OpeningType.DOOR,
        height=80  # 6'8"
    )
    plan.add_opening(front_door)
    
    # Add window to living room (left wall)
    living_window = Opening(
        wall_id=w4.id,
        position=0.5,
        width=48,  # 4 feet
        opening_type=OpeningType.WINDOW,
        height=48,
        sill_height=36
    )
    plan.add_opening(living_window)
    
    # Add window to bedroom (right wall)
    bedroom_window = Opening(
        wall_id=w6.id,
        position=0.5,
        width=48,
        opening_type=OpeningType.WINDOW,
        height=48,
        sill_height=36
    )
    plan.add_opening(bedroom_window)
    
    # Add door between living room and bedroom
    interior_door = Opening(
        wall_id=w2.id,
        position=0.8,  # Near top
        width=32,
        opening_type=OpeningType.DOOR,
        height=80
    )
    plan.add_opening(interior_door)
    
    # Add rooms
    living_room = Room(
        name="Living Room",
        wall_ids=[w1.id, w2.id, w3.id, w4.id],
        color="#FFE4B5"  # Light peach
    )
    plan.add_room(living_room)
    
    bedroom = Room(
        name="Bedroom",
        wall_ids=[w5.id, w6.id, w7.id, w2.id],
        color="#B0E0E6"  # Light blue
    )
    plan.add_room(bedroom)
    
    return plan


def create_l_shaped_house():
    """
    Create an L-shaped house with multiple rooms.
    
    More complex example showing:
    - Non-rectangular layout
    - Multiple rooms
    - Various wall types
    """
    
    plan = FloorPlan(name="L-Shaped House")
    
    def ft(feet):
        return feet * 12
    
    # Main rectangle (horizontal part of L)
    walls = [
        Wall(Point(0, 0), Point(ft(30), 0), 6, WallType.EXTERIOR),           # Bottom
        Wall(Point(ft(30), 0), Point(ft(30), ft(20)), 6, WallType.EXTERIOR), # Right
        Wall(Point(ft(30), ft(20)), Point(ft(15), ft(20)), 6, WallType.EXTERIOR), # Top-right
        Wall(Point(ft(15), ft(20)), Point(ft(15), ft(10)), 6, WallType.EXTERIOR), # Interior corner
        Wall(Point(ft(15), ft(10)), Point(0, ft(10)), 6, WallType.EXTERIOR),      # Top-left
        Wall(Point(0, ft(10)), Point(0, 0), 6, WallType.EXTERIOR),                # Left
    ]
    
    for wall in walls:
        plan.add_wall(wall)
    
    # Interior walls to divide rooms
    # Vertical divider in main section
    interior_wall_1 = Wall(
        Point(ft(15), 0), Point(ft(15), ft(20)),
        4, WallType.INTERIOR
    )
    plan.add_wall(interior_wall_1)
    
    # Horizontal divider in right section
    interior_wall_2 = Wall(
        Point(ft(15), ft(10)), Point(ft(30), ft(10)),
        4, WallType.INTERIOR
    )
    plan.add_wall(interior_wall_2)
    
    print(f"Created floor plan: {plan.name}")
    print(f"  - {len(plan.walls)} walls")
    print(f"  - {len(plan.openings)} openings")
    print(f"  - {len(plan.rooms)} rooms")
    
    return plan


def main():
    """Main example function."""
    print("=" * 60)
    print("Floor Plan Programmatic Creation Example")
    print("=" * 60)
    
    # Create simple house
    simple_house = create_simple_house()
    
    # Save to file
    output_dir = Path(__file__).parent
    simple_output = output_dir / "simple_house.floorplan"
    simple_house.save_to_file(str(simple_output))
    print(f"\n✓ Saved simple house to: {simple_output}")
    
    # Print summary
    print(f"\nSimple House Summary:")
    print(f"  - {len(simple_house.walls)} walls")
    print(f"  - {len(simple_house.openings)} openings ({sum(1 for o in simple_house.openings if o.opening_type == OpeningType.DOOR)} doors, {sum(1 for o in simple_house.openings if o.opening_type == OpeningType.WINDOW)} windows)")
    print(f"  - {len(simple_house.rooms)} rooms")
    
    # Calculate total wall length
    total_length = sum(wall.length() for wall in simple_house.walls)
    print(f"  - Total wall length: {total_length/12:.1f} feet ({total_length:.0f} inches)")
    
    # Get bounds
    bounds = simple_house.get_bounds()
    if bounds:
        min_pt, max_pt = bounds
        width = (max_pt.x - min_pt.x) / 12
        height = (max_pt.y - min_pt.y) / 12
        print(f"  - Dimensions: {width:.1f}' × {height:.1f}'")
        print(f"  - Area: {width * height:.1f} sq ft")
    
    print("\n" + "=" * 60)
    
    # Create L-shaped house
    l_house = create_l_shaped_house()
    l_output = output_dir / "l_shaped_house.floorplan"
    l_house.save_to_file(str(l_output))
    print(f"\n✓ Saved L-shaped house to: {l_output}")
    
    print("\n" + "=" * 60)
    print("Example complete! Open the generated files in the GUI:")
    print(f"  python main.py {simple_output}")
    print(f"  python main.py {l_output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
