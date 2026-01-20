#!/usr/bin/env python3
"""
Test RoomPlan JSON import functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import import_roomplan_json

def test_roomplan_import():
    """Test importing the office.json file."""
    
    print("="*60)
    print("Testing RoomPlan JSON Import")
    print("="*60)
    
    # Path to the office.json file
    test_file = "/mnt/user-data/uploads/office.json"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"\n1. Importing RoomPlan JSON: {test_file}")
    
    try:
        floor_plan = import_roomplan_json(test_file)
        
        print(f"\n2. Import successful!")
        print(f"   Name: {floor_plan.name}")
        print(f"   Floor level: {floor_plan.floor_level}")
        print(f"   Ceiling height: {floor_plan.ceiling_height:.1f}\"")
        
        print(f"\n3. Imported elements:")
        print(f"   Walls: {len(floor_plan.walls)}")
        print(f"   Doors: {len([o for o in floor_plan.openings if 'DOOR' in o.opening_type.value])}")
        print(f"   Windows: {len([o for o in floor_plan.openings if 'WINDOW' in o.opening_type.value])}")
        print(f"   Furniture: {len(floor_plan.furniture)}")
        print(f"   Fixtures: {len(floor_plan.fixtures)}")
        
        if floor_plan.walls:
            print(f"\n4. Wall details:")
            for i, wall in enumerate(floor_plan.walls[:3], 1):  # Show first 3 walls
                length = wall.length()
                print(f"   Wall {i}: {wall.start} to {wall.end}")
                print(f"           Length: {length:.1f}\" ({length/12:.1f}' or {length/39.37:.2f}m)")
                print(f"           Height: {wall.height:.1f}\"")
            
            if len(floor_plan.walls) > 3:
                print(f"   ... and {len(floor_plan.walls) - 3} more walls")
        
        if floor_plan.furniture:
            print(f"\n5. Furniture details:")
            for i, furn in enumerate(floor_plan.furniture[:3], 1):
                print(f"   {i}. {furn.furniture_type.value} at ({furn.position.x:.1f}\", {furn.position.y:.1f}\")")
                print(f"      Size: {furn.width:.1f}\" x {furn.depth:.1f}\"")
            
            if len(floor_plan.furniture) > 3:
                print(f"   ... and {len(floor_plan.furniture) - 3} more items")
        
        if floor_plan.fixtures:
            print(f"\n6. Fixture details:")
            for i, fix in enumerate(floor_plan.fixtures, 1):
                print(f"   {i}. {fix.fixture_type.value} at ({fix.position.x:.1f}\", {fix.position.y:.1f}\")")
                print(f"      Size: {fix.width:.1f}\" x {fix.depth:.1f}\"")
        
        # Test saving
        print(f"\n7. Testing save...")
        output_path = "/tmp/test_imported_office.floorplan"
        floor_plan.save_to_file(output_path)
        print(f"   ✓ Saved to: {output_path}")
        
        # Test loading back
        print(f"\n8. Testing load...")
        from core import FloorPlan
        loaded = FloorPlan.load_from_file(output_path)
        print(f"   ✓ Loaded back: {len(loaded.walls)} walls, {len(loaded.furniture)} furniture")
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_roomplan_import()
    sys.exit(0 if success else 1)
