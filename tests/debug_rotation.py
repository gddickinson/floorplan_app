"""
Debug script to check rotation extraction from RoomPlan JSON.
Run this to see what rotation values are in your scan file.
"""

import json
import math
from pathlib import Path

def extract_rotation_from_matrix(transform):
    """Extract rotation from transform matrix."""
    matrix = transform.get('matrix', None)
    
    print(f"\n--- Transform Debug ---")
    print(f"Full transform: {transform}")
    
    if not matrix:
        print("No matrix found!")
        return 0.0
    
    print(f"Matrix: {matrix}")
    print(f"Matrix length: {len(matrix)}")
    if len(matrix) > 0:
        print(f"First row: {matrix[0]}")
        print(f"First row length: {len(matrix[0])}")
    
    if not matrix or len(matrix) < 1 or len(matrix[0]) < 3:
        print("Matrix too short!")
        return 0.0
    
    try:
        # Extract the X-axis direction vector from the first row
        right_x = matrix[0][0]
        right_z = matrix[0][2]
        
        print(f"Right vector: ({right_x}, {right_z})")
        
        # Calculate angle using atan2
        angle_radians = math.atan2(-right_z, right_x)
        angle_degrees = math.degrees(angle_radians)
        
        print(f"Angle (raw): {angle_degrees}°")
        
        # Normalize to 0-360
        if angle_degrees < 0:
            angle_degrees += 360
        
        print(f"Angle (normalized): {angle_degrees}°")
        
        return angle_degrees
        
    except Exception as e:
        print(f"Error: {e}")
        return 0.0

def analyze_roomplan_file(filepath):
    """Analyze a RoomPlan JSON file."""
    print(f"Analyzing: {filepath}\n")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Check structure
    print(f"Top-level keys: {data.keys()}\n")
    
    # Find objects
    objects = data.get('objects', [])
    print(f"Found {len(objects)} objects\n")
    
    for i, obj in enumerate(objects):
        category = obj.get('category', 'unknown')
        print(f"\n{'='*60}")
        print(f"Object {i+1}: {category}")
        print(f"{'='*60}")
        
        # Get transform
        transform = obj.get('transform', {})
        rotation = extract_rotation_from_matrix(transform)
        
        print(f"\n→ EXTRACTED ROTATION: {rotation}°\n")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Default to office2.json if available
        filepath = '/Users/george/Documents/python_projects/floorplan_app/data/iphone_scans/office2.json'
    
    try:
        analyze_roomplan_file(filepath)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        print("\nUsage: python debug_rotation.py <path_to_roomplan.json>")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
