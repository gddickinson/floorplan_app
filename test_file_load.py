#!/usr/bin/env python3
"""
Test file loading and Building synchronization.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Building, FloorPlan, Wall, Point

def test_file_load_sync():
    """Test that loading a file properly syncs with Building."""
    
    print("="*60)
    print("Testing File Load and Building Synchronization")
    print("="*60)
    
    # Step 1: Create a floor plan with some walls
    print("\n1. Creating test floor plan with walls...")
    floor_plan = FloorPlan(name="Test Floor", floor_level=0)
    
    # Add some walls
    floor_plan.add_wall(Wall(Point(0, 0), Point(120, 0), 6))
    floor_plan.add_wall(Wall(Point(120, 0), Point(120, 120), 6))
    floor_plan.add_wall(Wall(Point(120, 120), Point(0, 120), 6))
    floor_plan.add_wall(Wall(Point(0, 120), Point(0, 0), 6))
    
    print(f"   Created floor plan with {len(floor_plan.walls)} walls")
    
    # Step 2: Save to file
    test_file = Path("test_floor.floorplan")
    print(f"\n2. Saving to {test_file}...")
    floor_plan.save_to_file(str(test_file))
    print(f"   Saved successfully")
    
    # Step 3: Simulate what the app does on startup
    print("\n3. Simulating app startup...")
    building = Building(name="New Building")
    current_floor = building.get_floor(0)
    print(f"   Building created with {len(current_floor.walls)} walls on ground floor")
    
    # Step 4: Load file (old way - WRONG)
    print("\n4. Loading file (old broken way)...")
    loaded_floor_plan = FloorPlan.load_from_file(str(test_file))
    print(f"   Loaded floor plan has {len(loaded_floor_plan.walls)} walls")
    print(f"   Building still has {len(building.get_floor(0).walls)} walls")
    print(f"   ✗ BROKEN: Building not updated!")
    
    # Step 5: Load file (new way - CORRECT)
    print("\n5. Loading file (new correct way)...")
    building2 = Building(name="New Building")
    loaded_floor_plan2 = FloorPlan.load_from_file(str(test_file))
    building2.floors[loaded_floor_plan2.floor_level] = loaded_floor_plan2
    
    print(f"   Loaded floor plan has {len(loaded_floor_plan2.walls)} walls")
    print(f"   Building now has {len(building2.get_floor(0).walls)} walls")
    
    if len(building2.get_floor(0).walls) == 4:
        print(f"   ✓ SUCCESS: Building properly updated!")
    else:
        print(f"   ✗ FAILURE: Building not synced")
    
    # Step 6: Verify they're the same object
    print("\n6. Verifying object references...")
    floor_from_building = building2.get_floor(0)
    print(f"   loaded_floor_plan2 is building2.floors[0]: {loaded_floor_plan2 is floor_from_building}")
    print(f"   Both have same walls: {len(loaded_floor_plan2.walls) == len(floor_from_building.walls)}")
    
    # Cleanup
    test_file.unlink()
    print(f"\n7. Cleaned up test file")
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60)

if __name__ == "__main__":
    test_file_load_sync()
