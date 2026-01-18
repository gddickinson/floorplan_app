#!/usr/bin/env python3
"""
Example: Complete House with All Object Types

Demonstrates all new features in version 1.2:
- Different door types (single, double, french, sliding, etc.)
- Different window types (single, double, bay, casement, etc.)
- Wall styles (solid, brick, glass, etc.)
- Furniture (beds, sofas, tables, chairs, etc.)
- Fixtures (kitchen, bathroom, laundry appliances)
- Stairs (straight, L-shaped, spiral, etc.)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    Point, Wall, WallType, WallStyle, Opening, OpeningType,
    Room, FloorPlan, Furniture, FurnitureType, Fixture, FixtureType,
    Stair, StairType
)


def create_comprehensive_house():
    """Create a complete house showcasing all object types."""
    plan = FloorPlan(name="Comprehensive House - All Features")
    
    def ft(feet):
        return feet * 12
    
    print("Creating comprehensive house with all object types...")
    
    # =========================================================================
    # FIRST FLOOR LAYOUT
    # =========================================================================
    
    # Living Room (20' x 18') - Left side
    print("\n1. Creating Living Room...")
    w1 = Wall(Point(0, 0), Point(ft(20), 0), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w2 = Wall(Point(ft(20), 0), Point(ft(20), ft(18)), 6, WallType.INTERIOR, WallStyle.SOLID)
    w3 = Wall(Point(ft(20), ft(18)), Point(0, ft(18)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w4 = Wall(Point(0, ft(18)), Point(0, 0), 8, WallType.EXTERIOR, WallStyle.BRICK)
    
    plan.add_wall(w1)
    plan.add_wall(w2)
    plan.add_wall(w3)
    plan.add_wall(w4)
    
    # Add French doors to living room
    plan.add_opening(Opening(w1.id, 0.5, 72, OpeningType.DOOR_FRENCH, height=84))
    # Add bay window
    plan.add_opening(Opening(w3.id, 0.5, 96, OpeningType.WINDOW_BAY, sill_height=36))
    # Add casement windows
    plan.add_opening(Opening(w4.id, 0.3, 48, OpeningType.WINDOW_CASEMENT, sill_height=36))
    plan.add_opening(Opening(w4.id, 0.7, 48, OpeningType.WINDOW_CASEMENT, sill_height=36))
    
    living_room = Room(name="Living Room", wall_ids=[w1.id, w2.id, w3.id, w4.id], color="#FFE4B5")
    plan.add_room(living_room)
    
    # Add furniture to living room
    plan.add_furniture(Furniture(Point(ft(10), ft(9)), 84, 36, FurnitureType.SOFA, rotation=90))
    plan.add_furniture(Furniture(Point(ft(15), ft(5)), 36, 36, FurnitureType.ARMCHAIR))
    plan.add_furniture(Furniture(Point(ft(15), ft(13)), 36, 36, FurnitureType.ARMCHAIR))
    plan.add_furniture(Furniture(Point(ft(10), ft(5)), 48, 24, FurnitureType.TABLE_COFFEE))
    plan.add_furniture(Furniture(Point(ft(16), ft(16)), 60, 18, FurnitureType.TV_STAND, rotation=270))
    
    # Kitchen (15' x 12') - Right of living room
    print("2. Creating Kitchen...")
    w5 = Wall(Point(ft(20), 0), Point(ft(35), 0), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w6 = Wall(Point(ft(35), 0), Point(ft(35), ft(12)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w7 = Wall(Point(ft(35), ft(12)), Point(ft(20), ft(12)), 6, WallType.INTERIOR, WallStyle.SOLID)
    
    plan.add_wall(w5)
    plan.add_wall(w6)
    plan.add_wall(w7)
    
    # Add sliding door to kitchen (patio access)
    plan.add_opening(Opening(w6.id, 0.7, 72, OpeningType.DOOR_SLIDING, height=84))
    # Add double-hung windows
    plan.add_opening(Opening(w5.id, 0.5, 60, OpeningType.WINDOW_DOUBLE, sill_height=36))
    # Add door to hallway
    plan.add_opening(Opening(w7.id, 0.2, 36, OpeningType.DOOR_SINGLE))
    
    kitchen = Room(name="Kitchen", wall_ids=[w5.id, w6.id, w7.id, w2.id], color="#F0E68C")
    plan.add_room(kitchen)
    
    # Add kitchen fixtures
    plan.add_fixture(Fixture(Point(ft(22), ft(2)), 36, 30, FixtureType.REFRIGERATOR))
    plan.add_fixture(Fixture(Point(ft(27), ft(2)), 30, 24, FixtureType.STOVE))
    plan.add_fixture(Fixture(Point(ft(32), ft(2)), 24, 24, FixtureType.DISHWASHER))
    plan.add_fixture(Fixture(Point(ft(29), ft(2)), 33, 22, FixtureType.SINK_KITCHEN, rotation=270))
    plan.add_fixture(Fixture(Point(ft(22), ft(10)), 30, 16, FixtureType.MICROWAVE))
    
    # Dining Area (12' x 12') - Upper right
    print("3. Creating Dining Area...")
    w8 = Wall(Point(ft(20), ft(12)), Point(ft(20), ft(18)), 6, WallType.INTERIOR, WallStyle.SOLID)
    w9 = Wall(Point(ft(20), ft(18)), Point(ft(32), ft(18)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w10 = Wall(Point(ft(32), ft(18)), Point(ft(32), ft(12)), 6, WallType.INTERIOR, WallStyle.SOLID)
    
    plan.add_wall(w8)
    plan.add_wall(w9)
    plan.add_wall(w10)
    
    # Add picture window
    plan.add_opening(Opening(w9.id, 0.5, 72, OpeningType.WINDOW_PICTURE, sill_height=36))
    # Add archway to living room
    plan.add_opening(Opening(w8.id, 0.5, 48, OpeningType.ARCHWAY, height=84))
    
    dining_area = Room(name="Dining Area", wall_ids=[w7.id, w8.id, w9.id, w10.id], color="#E6E6FA")
    plan.add_room(dining_area)
    
    # Add dining furniture
    plan.add_furniture(Furniture(Point(ft(26), ft(15)), 72, 36, FurnitureType.TABLE_DINING))
    plan.add_furniture(Furniture(Point(ft(30), ft(13)), 24, 24, FurnitureType.CHAIR))
    plan.add_furniture(Furniture(Point(ft(22), ft(13)), 24, 24, FurnitureType.CHAIR))
    plan.add_furniture(Furniture(Point(ft(30), ft(17)), 24, 24, FurnitureType.CHAIR))
    plan.add_furniture(Furniture(Point(ft(22), ft(17)), 24, 24, FurnitureType.CHAIR))
    
    # Master Bedroom (14' x 14') - Far right
    print("4. Creating Master Bedroom...")
    w11 = Wall(Point(ft(32), ft(12)), Point(ft(46), ft(12)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w12 = Wall(Point(ft(46), ft(12)), Point(ft(46), ft(26)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w13 = Wall(Point(ft(46), ft(26)), Point(ft(32), ft(26)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w14 = Wall(Point(ft(32), ft(26)), Point(ft(32), ft(18)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    
    plan.add_wall(w11)
    plan.add_wall(w12)
    plan.add_wall(w13)
    plan.add_wall(w14)
    
    # Add double door entry
    plan.add_opening(Opening(w10.id, 0.5, 60, OpeningType.DOOR_DOUBLE))
    # Add slider windows
    plan.add_opening(Opening(w12.id, 0.3, 48, OpeningType.WINDOW_SLIDER, sill_height=36))
    plan.add_opening(Opening(w12.id, 0.7, 48, OpeningType.WINDOW_SLIDER, sill_height=36))
    plan.add_opening(Opening(w13.id, 0.5, 60, OpeningType.WINDOW_DOUBLE, sill_height=36))
    
    master_bedroom = Room(name="Master Bedroom", wall_ids=[w10.id, w11.id, w12.id, w13.id, w14.id], color="#FFB6C1")
    plan.add_room(master_bedroom)
    
    # Add bedroom furniture
    plan.add_furniture(Furniture(Point(ft(39), ft(19)), 76, 80, FurnitureType.BED_KING))
    plan.add_furniture(Furniture(Point(ft(34), ft(16)), 24, 18, FurnitureType.NIGHTSTAND))
    plan.add_furniture(Furniture(Point(ft(44), ft(16)), 24, 18, FurnitureType.NIGHTSTAND))
    plan.add_furniture(Furniture(Point(ft(40), ft(24)), 48, 18, FurnitureType.DRESSER))
    plan.add_furniture(Furniture(Point(ft(35), ft(24)), 60, 30, FurnitureType.DESK))
    
    # Master Bathroom (8' x 10')
    print("5. Creating Master Bathroom...")
    w15 = Wall(Point(ft(32), ft(12)), Point(ft(32), ft(2)), 6, WallType.INTERIOR, WallStyle.SOLID)
    w16 = Wall(Point(ft(32), ft(2)), Point(ft(40), ft(2)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w17 = Wall(Point(ft(40), ft(2)), Point(ft(40), ft(12)), 6, WallType.INTERIOR, WallStyle.SOLID)
    
    plan.add_wall(w15)
    plan.add_wall(w16)
    plan.add_wall(w17)
    
    # Add pocket door for space saving
    plan.add_opening(Opening(w17.id, 0.5, 30, OpeningType.DOOR_POCKET))
    # Add awning window for ventilation
    plan.add_opening(Opening(w16.id, 0.5, 36, OpeningType.WINDOW_AWNING, sill_height=60))
    
    master_bath = Room(name="Master Bath", wall_ids=[w11.id, w15.id, w16.id, w17.id], color="#B0E0E6")
    plan.add_room(master_bath)
    
    # Add bathroom fixtures
    plan.add_fixture(Fixture(Point(ft(34), ft(3)), 20, 30, FixtureType.TOILET, rotation=90))
    plan.add_fixture(Fixture(Point(ft(38), ft(3)), 60, 22, FixtureType.SINK_DOUBLE, rotation=270))
    plan.add_fixture(Fixture(Point(ft(36), ft(10)), 60, 32, FixtureType.BATHTUB))
    plan.add_fixture(Fixture(Point(ft(34), ft(7)), 36, 36, FixtureType.SHOWER_CORNER))
    
    # Guest Bedroom (12' x 12')
    print("6. Creating Guest Bedroom...")
    w18 = Wall(Point(ft(40), ft(2)), Point(ft(52), ft(2)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w19 = Wall(Point(ft(52), ft(2)), Point(ft(52), ft(12)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w20 = Wall(Point(ft(52), ft(12)), Point(ft(46), ft(12)), 6, WallType.INTERIOR, WallStyle.SOLID)
    w21 = Wall(Point(ft(46), ft(12)), Point(ft(46), ft(2)), 6, WallType.INTERIOR, WallStyle.SOLID)
    
    plan.add_wall(w18)
    plan.add_wall(w19)
    plan.add_wall(w20)
    plan.add_wall(w21)
    
    # Add bifold closet door
    plan.add_opening(Opening(w21.id, 0.5, 60, OpeningType.DOOR_BIFOLD))
    # Add single door entry
    plan.add_opening(Opening(w20.id, 0.7, 32, OpeningType.DOOR_SINGLE))
    # Add windows
    plan.add_opening(Opening(w18.id, 0.5, 48, OpeningType.WINDOW_SINGLE, sill_height=36))
    plan.add_opening(Opening(w19.id, 0.5, 48, OpeningType.WINDOW_SINGLE, sill_height=36))
    
    guest_bedroom = Room(name="Guest Bedroom", wall_ids=[w17.id, w18.id, w19.id, w20.id], color="#DDA0DD")
    plan.add_room(guest_bedroom)
    
    # Add guest bedroom furniture
    plan.add_furniture(Furniture(Point(ft(47), ft(7)), 60, 80, FurnitureType.BED_QUEEN))
    plan.add_furniture(Furniture(Point(ft(44), ft(4)), 24, 18, FurnitureType.NIGHTSTAND))
    plan.add_furniture(Furniture(Point(ft(50), ft(4)), 24, 18, FurnitureType.NIGHTSTAND))
    plan.add_furniture(Furniture(Point(ft(51), ft(10)), 36, 12, FurnitureType.BOOKSHELF))
    
    # Hallway with stairs
    print("7. Creating Hallway and Stairs...")
    w22 = Wall(Point(ft(40), ft(12)), Point(ft(52), ft(12)), 6, WallType.INTERIOR, WallStyle.SOLID)
    
    plan.add_wall(w22)
    
    # Add straight staircase to second floor
    stair = Stair(
        start=Point(ft(42), ft(12)),
        end=Point(ft(42), ft(22)),
        width=36,
        stair_type=StairType.STRAIGHT,
        num_steps=14
    )
    plan.add_stair(stair)
    
    # Laundry Room (6' x 8')
    print("8. Creating Laundry Room...")
    w23 = Wall(Point(ft(35), ft(0)), Point(ft(41), ft(0)), 8, WallType.EXTERIOR, WallStyle.BRICK)
    w24 = Wall(Point(ft(41), ft(0)), Point(ft(41), ft(2)), 6, WallType.INTERIOR, WallStyle.SOLID)
    w25 = Wall(Point(ft(35), ft(0)), Point(ft(35), ft(2)), 6, WallType.INTERIOR, WallStyle.SOLID)
    
    plan.add_wall(w23)
    plan.add_wall(w24)
    plan.add_wall(w25)
    
    # Add Dutch door (half door) for fun
    plan.add_opening(Opening(w25.id, 0.5, 32, OpeningType.DOOR_DUTCH))
    
    laundry = Room(name="Laundry", wall_ids=[w5.id, w23.id, w24.id, w16.id, w25.id], color="#F5DEB3")
    plan.add_room(laundry)
    
    # Add laundry fixtures
    plan.add_fixture(Fixture(Point(ft(36), ft(1)), 27, 28, FixtureType.WASHER))
    plan.add_fixture(Fixture(Point(ft(39), ft(1)), 27, 28, FixtureType.DRYER))
    
    # Garage (20' x 20')
    print("9. Creating Garage...")
    w26 = Wall(Point(ft(0), ft(18)), Point(ft(0), ft(38)), 8, WallType.EXTERIOR, WallStyle.CONCRETE)
    w27 = Wall(Point(ft(0), ft(38)), Point(ft(20), ft(38)), 8, WallType.EXTERIOR, WallStyle.CONCRETE)
    w28 = Wall(Point(ft(20), ft(38)), Point(ft(20), ft(18)), 8, WallType.INTERIOR, WallStyle.CONCRETE)
    
    plan.add_wall(w26)
    plan.add_wall(w27)
    plan.add_wall(w28)
    
    # Add garage door
    plan.add_opening(Opening(w27.id, 0.5, 192, OpeningType.DOOR_GARAGE, height=84))
    # Add door to house
    plan.add_opening(Opening(w28.id, 0.8, 32, OpeningType.DOOR_SINGLE))
    
    garage = Room(name="Garage", wall_ids=[w3.id, w26.id, w27.id, w28.id], color="#D3D3D3")
    plan.add_room(garage)
    
    # Add HVAC equipment in garage
    plan.add_fixture(Fixture(Point(ft(2), ft(36)), 24, 24, FixtureType.WATER_HEATER))
    plan.add_fixture(Fixture(Point(ft(5), ft(36)), 36, 30, FixtureType.FURNACE))
    
    return plan


def print_summary(plan):
    """Print summary of the floor plan."""
    print("\n" + "="*70)
    print("FLOOR PLAN SUMMARY")
    print("="*70)
    
    print(f"\nName: {plan.name}")
    print(f"Walls: {len(plan.walls)}")
    print(f"  - Exterior: {sum(1 for w in plan.walls if w.wall_type == WallType.EXTERIOR)}")
    print(f"  - Interior: {sum(1 for w in plan.walls if w.wall_type == WallType.INTERIOR)}")
    
    print(f"\nOpenings: {len(plan.openings)}")
    # Count by type
    from collections import Counter
    opening_types = Counter(o.opening_type.value for o in plan.openings)
    for opening_type, count in sorted(opening_types.items()):
        print(f"  - {opening_type}: {count}")
    
    print(f"\nRooms: {len(plan.rooms)}")
    for room in plan.rooms:
        print(f"  - {room.name}")
    
    print(f"\nFurniture: {len(plan.furniture)}")
    furniture_types = Counter(f.furniture_type.value for f in plan.furniture)
    for furn_type, count in sorted(furniture_types.items()):
        print(f"  - {furn_type}: {count}")
    
    print(f"\nFixtures: {len(plan.fixtures)}")
    fixture_types = Counter(f.fixture_type.value for f in plan.fixtures)
    for fix_type, count in sorted(fixture_types.items()):
        print(f"  - {fix_type}: {count}")
    
    print(f"\nStairs: {len(plan.stairs)}")
    for stair in plan.stairs:
        print(f"  - {stair.stair_type.value}: {stair.num_steps} steps")


def main():
    """Main function."""
    print("="*70)
    print("COMPREHENSIVE HOUSE EXAMPLE - ALL FEATURES")
    print("="*70)
    
    # Create the house
    plan = create_comprehensive_house()
    
    # Print summary
    print_summary(plan)
    
    # Save to file
    output_dir = Path(__file__).parent
    output_file = output_dir / "comprehensive_house.floorplan"
    plan.save_to_file(str(output_file))
    
    print("\n" + "="*70)
    print(f"✓ Saved to: {output_file}")
    print("\nOpen in GUI to see:")
    print("  - Different door types (french, sliding, pocket, bifold, etc.)")
    print("  - Different window types (bay, casement, slider, picture, etc.)")
    print("  - Wall styles (brick, concrete, solid)")
    print("  - Complete furniture layout")
    print("  - Kitchen and bathroom fixtures")
    print("  - Laundry appliances")
    print("  - Staircase to second floor")
    print("  - HVAC equipment")
    print(f"\nCommand: python main.py {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
