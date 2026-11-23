#!/usr/bin/env python3
"""
Synthetic 3D Pointcloud Generator for Dreame A2 Community Cockpit.
Generates an artificial demo garden (lawn, trees, pathway, perimeter fence)
to demonstrate 3D LiDAR rendering without exposing any real property data.
"""

import math
import random
import os

def generate_synthetic_garden_pcd(output_path: str, num_points: int = 15000):
    points = []
    
    # 1. Lawn terrain: 20m x 15m rectangle with slight undulation
    for _ in range(int(num_points * 0.70)):
        x = random.uniform(-10.0, 10.0)
        y = random.uniform(-7.5, 7.5)
        # Gentle terrain elevation curve
        z = 0.05 * math.sin(x * 0.3) + 0.03 * math.cos(y * 0.4) + random.uniform(-0.015, 0.015)
        # Intensity based on grass density
        intensity = random.uniform(20.0, 45.0)
        points.append((x, y, z, intensity))
        
    # 2. Paved terrace & stone path (x from -8 to -4, y from -7.5 to -3)
    for _ in range(int(num_points * 0.12)):
        x = random.uniform(-8.0, -4.0)
        y = random.uniform(-7.5, -3.0)
        z = 0.08 + random.uniform(-0.005, 0.005) # Slightly elevated flat terrace
        intensity = random.uniform(60.0, 85.0) # Stone higher reflectivity
        points.append((x, y, z, intensity))
        
    # 3. Two synthetic trees (cylindrical trunk + spherical canopy)
    tree_centers = [(4.0, 2.5), (-2.0, 4.0)]
    for tx, ty in tree_centers:
        # Canopy points
        for _ in range(int(num_points * 0.06)):
            u = random.uniform(0, 1)
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 1.2 * (u ** (1/3))
            px = tx + r * math.sin(phi) * math.cos(theta)
            py = ty + r * math.sin(phi) * math.sin(theta)
            pz = 1.8 + r * math.cos(phi)
            intensity = random.uniform(15.0, 35.0)
            points.append((px, py, pz, intensity))
            
    # 4. Perimeter wooden fence / hedge
    for _ in range(int(num_points * 0.06)):
        edge = random.choice(['N', 'S', 'E', 'W'])
        if edge == 'N':
            x = random.uniform(-10.0, 10.0)
            y = 7.5
        elif edge == 'S':
            x = random.uniform(-10.0, 10.0)
            y = -7.5
        elif edge == 'E':
            x = 10.0
            y = random.uniform(-7.5, 7.5)
        else:
            x = -10.0
            y = random.uniform(-7.5, 7.5)
        z = random.uniform(0.0, 1.2) # Fence height
        intensity = random.uniform(40.0, 70.0)
        points.append((x, y, z, intensity))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with open(output_path, "w", encoding="ascii") as f:
        f.write("# .PCD v0.7 - Point Cloud Data file format\n")
        f.write("VERSION 0.7\n")
        f.write("FIELDS x y z intensity\n")
        f.write("SIZE 4 4 4 4\n")
        f.write("TYPE F F F F\n")
        f.write("COUNT 1 1 1 1\n")
        f.write(f"WIDTH {len(points)}\n")
        f.write("HEIGHT 1\n")
        f.write("VIEWPOINT 0 0 0 1 0 0 0\n")
        f.write(f"POINTS {len(points)}\n")
        f.write("DATA ascii\n")
        for p in points:
            f.write(f"{p[0]:.3f} {p[1]:.3f} {p[2]:.3f} {p[3]:.1f}\n")
            
    print(f"✅ Generated {len(points)} synthetic points into: {output_path}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "web/assets/demo_garden.pcd"
    generate_synthetic_garden_pcd(out)
