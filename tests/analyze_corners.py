"""
iPhone Scan Corner Analyzer

Analyzes corner gaps in iPhone scan data to help diagnose import issues.
"""

import json
import math
from typing import List, Tuple
from pathlib import Path


def analyze_scan_corners(filepath: str):
    """
    Analyze corner gaps in iPhone scan JSON file.
    
    Args:
        filepath: Path to JSON scan file
    """
    print(f"Analyzing: {filepath}\n")
    print("="*70)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    walls = data.get('walls', [])
    print(f"\nFound {len(walls)} walls\n")
    
    METERS_TO_INCHES = 39.3701
    
    # Extract wall endpoints
    endpoints: List[Tuple[int, bool, float, float]] = []  # (wall_idx, is_start, x, z)
    
    for idx, wall in enumerate(walls):
        # Get wall dimensions and position
        dimensions = wall.get('dimensions', {})
        transform = wall.get('transform', {})
        position = transform.get('position', {})
        matrix = transform.get('matrix', [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
        
        width = dimensions.get('width', 0) * METERS_TO_INCHES
        pos_x = position.get('x', 0) * METERS_TO_INCHES
        pos_z = position.get('z', 0) * METERS_TO_INCHES
        
        # Get wall direction from matrix
        right_x = matrix[0][0]
        right_z = matrix[0][2]
        length = math.sqrt(right_x * right_x + right_z * right_z)
        
        if length > 0.001:
            dir_x = right_x / length
            dir_z = right_z / length
        else:
            dir_x = 1.0
            dir_z = 0.0
        
        # Calculate endpoints
        half_width = width / 2
        start_x = pos_x - dir_x * half_width
        start_z = pos_z - dir_z * half_width
        end_x = pos_x + dir_x * half_width
        end_z = pos_z + dir_z * half_width
        
        endpoints.append((idx, True, start_x, start_z))
        endpoints.append((idx, False, end_x, end_z))
        
        print(f"Wall {idx}:")
        print(f"  Start: ({start_x:7.2f}\", {start_z:7.2f}\")")
        print(f"  End:   ({end_x:7.2f}\", {end_z:7.2f}\")")
        print(f"  Length: {width:.2f}\"")
    
    # Find close corners
    print("\n" + "="*70)
    print("\nCorner Proximity Analysis:\n")
    
    close_pairs = []
    
    for i in range(len(endpoints)):
        wall1_idx, is_start1, x1, z1 = endpoints[i]
        
        for j in range(i + 1, len(endpoints)):
            wall2_idx, is_start2, x2, z2 = endpoints[j]
            
            # Calculate distance
            dx = x1 - x2
            dz = z1 - z2
            distance = math.sqrt(dx * dx + dz * dz)
            
            # If close (within 12 inches), report it
            if distance < 12.0:
                close_pairs.append((distance, wall1_idx, is_start1, wall2_idx, is_start2, x1, z1, x2, z2))
    
    # Sort by distance
    close_pairs.sort()
    
    if not close_pairs:
        print("No corners within 12\" of each other found.")
        print("This might indicate walls are not forming a closed room.")
    else:
        print(f"Found {len(close_pairs)} corner pairs within 12\":\n")
        
        for dist, w1, s1, w2, s2, x1, z1, x2, z2 in close_pairs:
            endpoint1 = "start" if s1 else "end"
            endpoint2 = "start" if s2 else "end"
            
            print(f"Gap: {dist:6.3f}\"  ->  Wall {w1} {endpoint1} ↔ Wall {w2} {endpoint2}")
            print(f"  Point 1: ({x1:7.2f}\", {z1:7.2f}\")")
            print(f"  Point 2: ({x2:7.2f}\", {z2:7.2f}\")")
            
            if dist > 0.1:
                avg_x = (x1 + x2) / 2
                avg_z = (z1 + z2) / 2
                print(f"  Average: ({avg_x:7.2f}\", {avg_z:7.2f}\")  [SHOULD SNAP HERE]")
            print()
    
    # Statistics
    print("="*70)
    print("\nSummary:\n")
    
    gaps = [dist for dist, *_ in close_pairs if dist > 0.1]
    if gaps:
        print(f"Number of gaps: {len(gaps)}")
        print(f"Min gap: {min(gaps):.3f}\"")
        print(f"Max gap: {max(gaps):.3f}\"")
        print(f"Avg gap: {sum(gaps)/len(gaps):.3f}\"")
        print()
        print("Recommendation:")
        max_gap = max(gaps)
        recommended_tolerance = math.ceil(max_gap) + 1
        print(f"  Set corner_snap_tolerance = {recommended_tolerance}\" to fix all gaps")
    else:
        print("All corners are already perfectly connected!")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_corners.py <scan_file.json>")
        sys.exit(1)
    
    analyze_scan_corners(sys.argv[1])

