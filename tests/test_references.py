#!/usr/bin/env python3
"""
Test script to verify Building and FloorPlan reference synchronization.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Building, FloorPlan, Wall, Point

def test_references():
    """Test that floor plan references are properly synchronized."""
    
    print("="*60)
    print("Testing Building and FloorPlan Reference Synchronization")
    print("="*60)
    
    # Create building
    print("\n1. Creating building...")
    building = Building(name="Test Building")
    print(f"   Building created: {building.name}")
    print(f"   Floors in building: {list(building.floors.keys())}")
    
    # Get ground floor
    print("\n2. Getting ground floor...")
    floor_plan = building.get_floor(0)
    print(f"   Floor plan: {floor_plan.name if floor_plan else 'None'}")
    
    if floor_plan:
        print(f"   Walls in floor_plan: {len(floor_plan.walls)}")
        print(f"   Walls in building.floors[0]: {len(building.floors[0].walls)}")
        
        # Check if they're the same object
        print(f"\n3. Testing object identity...")
        print(f"   floor_plan is building.floors[0]: {floor_plan is building.floors[0]}")
        print(f"   id(floor_plan): {id(floor_plan)}")
        print(f"   id(building.floors[0]): {id(building.floors[0])}")
        
        # Add a wall to floor_plan
        print(f"\n4. Adding wall to floor_plan...")
        wall = Wall(
            start=Point(0, 0),
            end=Point(120, 0),
            thickness=6
        )
        floor_plan.add_wall(wall)
        
        print(f"   Walls in floor_plan: {len(floor_plan.walls)}")
        print(f"   Walls in building.floors[0]: {len(building.floors[0].walls)}")
        
        # Verify they both show the wall
        if len(floor_plan.walls) == 1 and len(building.floors[0].walls) == 1:
            print(f"   ✓ SUCCESS: Both references show the wall!")
        else:
            print(f"   ✗ FAILURE: References are not synchronized!")
            
        # Check wall identity
        print(f"\n5. Verifying wall is the same object...")
        print(f"   floor_plan.walls[0] is building.floors[0].walls[0]: {floor_plan.walls[0] is building.floors[0].walls[0]}")
    else:
        print("   ✗ FAILURE: No ground floor found!")
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60)

if __name__ == "__main__":
    test_references()

