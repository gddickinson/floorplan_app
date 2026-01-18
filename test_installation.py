#!/usr/bin/env python3
"""
Quick Test Script for Floor Plan Editor

Verifies that all dependencies are installed and core components work.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    errors = []
    
    # Test PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPainter
        print("  ✓ PyQt6 imported successfully")
    except ImportError as e:
        errors.append(f"PyQt6 import failed: {e}")
        print(f"  ✗ PyQt6 import failed: {e}")
    
    # Test core module
    try:
        from core import Point, Wall, Opening, Room, FloorPlan
        print("  ✓ Core module imported successfully")
    except ImportError as e:
        errors.append(f"Core module import failed: {e}")
        print(f"  ✗ Core module import failed: {e}")
    
    # Test utils module
    try:
        from utils import setup_logging, AppConfig
        print("  ✓ Utils module imported successfully")
    except ImportError as e:
        errors.append(f"Utils module import failed: {e}")
        print(f"  ✗ Utils module import failed: {e}")
    
    # Test GUI module
    try:
        from gui import MainWindow, FloorPlanCanvas
        print("  ✓ GUI module imported successfully")
    except ImportError as e:
        errors.append(f"GUI module import failed: {e}")
        print(f"  ✗ GUI module import failed: {e}")
    
    return errors


def test_geometry():
    """Test basic geometry operations."""
    print("\nTesting geometry...")
    
    from core import Point, Wall, FloorPlan
    
    # Test Point
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    dist = p1.distance_to(p2)
    assert abs(dist - 5.0) < 0.01, f"Distance calculation failed: {dist}"
    print(f"  ✓ Point distance calculation: {dist:.1f}")
    
    # Test Wall
    wall = Wall(p1, p2, thickness=6)
    assert abs(wall.length() - 5.0) < 0.01, f"Wall length failed: {wall.length()}"
    print(f"  ✓ Wall length calculation: {wall.length():.1f}")
    
    # Test FloorPlan
    plan = FloorPlan(name="Test Plan")
    wall_id = plan.add_wall(wall)
    assert len(plan.walls) == 1, "Wall addition failed"
    print(f"  ✓ Floor plan wall addition")
    
    # Test serialization
    plan_dict = plan.to_dict()
    assert plan_dict["name"] == "Test Plan", "Serialization failed"
    print(f"  ✓ Floor plan serialization")
    
    # Test deserialization
    plan2 = FloorPlan.from_dict(plan_dict)
    assert len(plan2.walls) == 1, "Deserialization failed"
    print(f"  ✓ Floor plan deserialization")
    
    return []


def test_file_io():
    """Test file save/load operations."""
    print("\nTesting file I/O...")
    
    from core import Point, Wall, FloorPlan
    import tempfile
    
    # Create a test plan
    plan = FloorPlan(name="Test I/O Plan")
    plan.add_wall(Wall(Point(0, 0), Point(100, 0)))
    plan.add_wall(Wall(Point(100, 0), Point(100, 100)))
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.floorplan', delete=False) as f:
        temp_path = f.name
    
    try:
        plan.save_to_file(temp_path)
        print(f"  ✓ Floor plan saved to temporary file")
        
        # Load from file
        loaded_plan = FloorPlan.load_from_file(temp_path)
        assert len(loaded_plan.walls) == 2, "Loaded plan has wrong number of walls"
        assert loaded_plan.name == "Test I/O Plan", "Loaded plan has wrong name"
        print(f"  ✓ Floor plan loaded from file")
        
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    return []


def main():
    """Run all tests."""
    print("=" * 60)
    print("Floor Plan Editor - Quick Test")
    print("=" * 60)
    
    all_errors = []
    
    # Run tests
    all_errors.extend(test_imports())
    
    if not all_errors:
        try:
            all_errors.extend(test_geometry())
            all_errors.extend(test_file_io())
        except Exception as e:
            all_errors.append(f"Test execution error: {e}")
            print(f"\n✗ Test execution error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print("TESTS FAILED")
        print("\nErrors found:")
        for error in all_errors:
            print(f"  - {error}")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1
    else:
        print("ALL TESTS PASSED ✓")
        print("\nYou're ready to run the application!")
        print("  python main.py")
        return 0


if __name__ == "__main__":
    sys.exit(main())
