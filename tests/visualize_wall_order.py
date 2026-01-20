"""
Wall Order Visualizer

Shows how walls connect before and after reordering.
"""

import json
import math
from typing import List, Tuple


def analyze_wall_order(filepath: str):
    """Analyze and visualize wall connectivity."""
    print(f"Analyzing: {filepath}\n")
    print("="*70)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    walls = data.get('walls', [])
    METERS_TO_INCHES = 39.3701
    
    # Extract wall data
    wall_data = []
    for idx, wall in enumerate(walls):
        dimensions = wall.get('dimensions', {})
        transform = wall.get('transform', {})
        position = transform.get('position', {})
        matrix = transform.get('matrix', [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]])
        
        width = dimensions.get('width', 0) * METERS_TO_INCHES
        pos_x = position.get('x', 0) * METERS_TO_INCHES
        pos_z = position.get('z', 0) * METERS_TO_INCHES
        
        right_x = matrix[0][0]
        right_z = matrix[0][2]
        length = math.sqrt(right_x * right_x + right_z * right_z)
        
        if length > 0.001:
            dir_x = right_x / length
            dir_z = right_z / length
        else:
            dir_x = 1.0
            dir_z = 0.0
        
        half_width = width / 2
        start_x = pos_x - dir_x * half_width
        start_z = pos_z - dir_z * half_width
        end_x = pos_x + dir_x * half_width
        end_z = pos_z + dir_z * half_width
        
        wall_data.append({
            'idx': idx,
            'start': (start_x, start_z),
            'end': (end_x, end_z),
            'length': width
        })
    
    # Print original order
    print("\nORIGINAL WALL ORDER:\n")
    for w in wall_data:
        print(f"Wall {w['idx']}: ({w['start'][0]:7.2f}\", {w['start'][1]:7.2f}\") → "
              f"({w['end'][0]:7.2f}\", {w['end'][1]:7.2f}\")")
    
    # Find connectivity
    print("\n" + "="*70)
    print("\nWALL CONNECTIVITY:\n")
    
    tolerance = 0.1
    connections = []
    
    for w1 in wall_data:
        for w2 in wall_data:
            if w1['idx'] == w2['idx']:
                continue
            
            # Check if w1's end connects to w2's start
            dist_end_start = math.sqrt(
                (w1['end'][0] - w2['start'][0])**2 + 
                (w1['end'][1] - w2['start'][1])**2
            )
            
            # Check if w1's end connects to w2's end  
            dist_end_end = math.sqrt(
                (w1['end'][0] - w2['end'][0])**2 +
                (w1['end'][1] - w2['end'][1])**2
            )
            
            if dist_end_start < tolerance:
                connections.append((w1['idx'], 'end', w2['idx'], 'start'))
                print(f"Wall {w1['idx']} end → Wall {w2['idx']} start  (gap: {dist_end_start:.3f}\")")
            elif dist_end_end < tolerance:
                connections.append((w1['idx'], 'end', w2['idx'], 'end'))
                print(f"Wall {w1['idx']} end → Wall {w2['idx']} end [REVERSED] (gap: {dist_end_end:.3f}\")")
    
    # Trace the path
    print("\n" + "="*70)
    print("\nWALL CHAIN PATH:\n")
    
    if not connections:
        print("No connections found!")
        return
    
    # Start with wall 0
    current_wall = 0
    current_end = 'end'
    visited = {current_wall}
    path = [current_wall]
    
    while len(visited) < len(wall_data):
        # Find next wall
        next_wall = None
        next_is_reversed = False
        
        for w1, e1, w2, e2 in connections:
            if w1 == current_wall and e1 == current_end and w2 not in visited:
                next_wall = w2
                next_is_reversed = (e2 == 'end')
                break
        
        if next_wall is None:
            print(f"  Chain breaks at Wall {current_wall}!")
            break
        
        path.append(next_wall)
        visited.add(next_wall)
        
        arrow = "→ (reversed)" if next_is_reversed else "→"
        print(f"  Wall {current_wall} {arrow} Wall {next_wall}")
        
        current_wall = next_wall
        current_end = 'end'
    
    print("\nCurrent path sequence:", " → ".join(f"Wall {w}" for w in path))
    
    # Suggested reordering
    print("\n" + "="*70)
    print("\nRECOMMENDED ACTIONS:\n")
    
    if path == list(range(len(wall_data))):
        print("✓ Walls are already in correct sequential order!")
    else:
        print("✗ Walls need reordering")
        print(f"  Current order: {list(range(len(wall_data)))}")
        print(f"  Connected path: {path}")
        print("\n  Use the iphone_scan_importer_ordered.py to fix this automatically.")
    
    # Check for reversed walls
    reversed_count = sum(1 for _, _, _, e2 in connections if e2 == 'end')
    if reversed_count > 0:
        print(f"\n✗ {reversed_count} wall(s) need direction reversal")
        print("  (Some walls connect end-to-end instead of end-to-start)")
        print("  The importer will flip these automatically.")
    else:
        print("\n✓ All walls have consistent direction")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python visualize_wall_order.py <scan_file.json>")
        sys.exit(1)
    
    analyze_wall_order(sys.argv[1])
