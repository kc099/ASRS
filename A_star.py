import heapq

# ============================================================================
# A* PATHFINDING - COMPLETE EXAMPLE WITH VISUALIZATION
# ============================================================================

def heuristic(pos, goal):
    """Manhattan distance - counts steps horizontally + vertically"""
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

def a_star_pathfinding(grid, start, goal):
    """
    Find shortest path from start to goal avoiding obstacles (X)
    
    grid: 2D list where:
        '.' = empty (can walk)
        'X' = obstacle (cannot walk)
    start: (row, col) starting position
    goal: (row, col) ending position
    
    Returns: path (list of positions) or None if no path exists
    """
    rows = len(grid)
    cols = len(grid[0])
    
    # Priority queue: (priority, cost, position, path)
    open_set = [(0, 0, start, [start])]
    visited = set()  # Track visited positions
    
    print(f"\n{'='*60}")
    print(f"🎯 FINDING PATH FROM {start} TO {goal}")
    print(f"{'='*60}\n")
    
    step = 0
    
    while open_set:
        # Get node with lowest priority (most promising)
        priority, cost, current, path = heapq.heappop(open_set)
        
        step += 1
        print(f"📍 Step {step}: At {current}, Cost={cost}, Priority={priority}")
        
        # Skip if already visited
        if current in visited:
            print(f"   ⏭️  Already visited, skipping")
            continue
        
        visited.add(current)
        
        # ✅ GOAL REACHED!
        if current == goal:
            print(f"\n{'='*60}")
            print(f"✅ PATH FOUND! Total steps: {cost}")
            print(f"{'='*60}")
            return path
        
        # Check 4 neighbors (up, down, left, right)
        directions = [
            (-1, 0, "⬆️ UP"),
            (1, 0, "⬇️ DOWN"),
            (0, -1, "⬅️ LEFT"),
            (0, 1, "➡️ RIGHT")
        ]
        
        for dr, dc, direction_name in directions:
            neighbor = (current[0] + dr, current[1] + dc)
            nr, nc = neighbor
            
            # Check bounds
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            
            # Check obstacle
            if grid[nr][nc] == 'X':
                continue
            
            # Skip if visited
            if neighbor in visited:
                continue
            
            # Calculate costs
            new_cost = cost + 1
            h = heuristic(neighbor, goal)
            new_priority = new_cost + h
            
            print(f"   {direction_name} → {neighbor}: cost={new_cost}, h={h}, priority={new_priority}")
            
            # Add to queue
            heapq.heappush(open_set, (new_priority, new_cost, neighbor, path + [neighbor]))
        
        print()
    
    print("\n❌ NO PATH FOUND!\n")
    return None

def print_grid_with_path(grid, path=None, start=None, goal=None):
    """Print grid with path visualization"""
    rows = len(grid)
    cols = len(grid[0])
    
    # Create copy of grid
    display = []
    for row in grid:
        display.append(list(row))
    
    # Mark path
    if path:
        for pos in path:
            r, c = pos
            if display[r][c] != 'S' and display[r][c] != 'E':
                display[r][c] = '•'
    
    # Mark start and goal
    if start:
        display[start[0]][start[1]] = 'S'
    if goal:
        display[goal[0]][goal[1]] = 'E'
    
    # Print
    print("\n" + "="*60)
    print("GRID LAYOUT:")
    print("="*60)
    print("  ", end="")
    for c in range(cols):
        print(f" {c}", end="")
    print()
    
    for r in range(rows):
        print(f"{r:2d} ", end="")
        for c in range(cols):
            cell = display[r][c]
            if cell == 'S':
                print(" 🚛", end="")  # Start (trolley)
            elif cell == 'E':
                print(" 🎯", end="")  # Goal
            elif cell == 'X':
                print(" 📦", end="")  # Obstacle (box)
            elif cell == '•':
                print(" ●", end="")  # Path
            else:
                print(" ·", end="")  # Empty
        print()
    print("="*60)
    print("Legend: 🚛=Start, 🎯=Goal, 📦=Box, ●=Path, ·=Empty\n")

# ============================================================================
# EXAMPLE 1: SIMPLE PATH (NO OBSTACLES)
# ============================================================================

print("\n" + "🔵"*30)
print("EXAMPLE 1: SIMPLE PATH - NO OBSTACLES")
print("🔵"*30)

grid1 = [
    ['.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.']
]

start1 = (0, 0)  # Top-left
goal1 = (4, 4)   # Bottom-right

print_grid_with_path(grid1, start=start1, goal=goal1)
path1 = a_star_pathfinding(grid1, start1, goal1)

if path1:
    print(f"\n📍 Final Path: {path1}")
    print(f"📏 Path Length: {len(path1)} steps")
    print_grid_with_path(grid1, path1, start1, goal1)

# ============================================================================
# EXAMPLE 2: PATH WITH OBSTACLES
# ============================================================================

print("\n" + "🟡"*30)
print("EXAMPLE 2: PATH AROUND OBSTACLES")
print("🟡"*30)

grid2 = [
    ['.', '.', '.', '.', '.'],
    ['.', 'X', 'X', 'X', '.'],
    ['.', '.', '.', 'X', '.'],
    ['.', 'X', '.', 'X', '.'],
    ['.', '.', '.', '.', '.']
]

start2 = (0, 0)  # Top-left
goal2 = (0, 4)   # Top-right

print_grid_with_path(grid2, start=start2, goal=goal2)
path2 = a_star_pathfinding(grid2, start2, goal2)

if path2:
    print(f"\n📍 Final Path: {path2}")
    print(f"📏 Path Length: {len(path2)} steps")
    print_grid_with_path(grid2, path2, start2, goal2)

# ============================================================================
# EXAMPLE 3: WAREHOUSE SCENARIO (LIKE YOUR ASRS)
# ============================================================================

print("\n" + "🟢"*30)
print("EXAMPLE 3: WAREHOUSE SCENARIO")
print("🟢"*30)

# Trolley at bottom-left, box at top-right
grid3 = [
    ['.', '.', '.', 'X', '.', '.', '.'],
    ['.', 'X', '.', 'X', '.', 'X', '.'],
    ['.', 'X', '.', '.', '.', 'X', '.'],
    ['.', '.', '.', 'X', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.']
]

start3 = (4, 0)  # Bottom-left (trolley origin)
goal3 = (0, 6)   # Top-right (box location)

print_grid_with_path(grid3, start=start3, goal=goal3)
path3 = a_star_pathfinding(grid3, start3, goal3)

if path3:
    print(f"\n📍 Final Path: {path3}")
    print(f"📏 Path Length: {len(path3)} steps")
    print(f"🚛 Trolley would travel: {len(path3) - 1} moves")
    print_grid_with_path(grid3, path3, start3, goal3)

# ============================================================================
# EXAMPLE 4: NO PATH POSSIBLE
# ============================================================================

print("\n" + "🔴"*30)
print("EXAMPLE 4: NO PATH (COMPLETELY BLOCKED)")
print("🔴"*30)

grid4 = [
    ['.', '.', '.', '.', '.'],
    ['.', 'X', 'X', 'X', '.'],
    ['.', 'X', '.', 'X', '.'],
    ['.', 'X', 'X', 'X', '.'],
    ['.', '.', '.', '.', '.']
]

start4 = (2, 2)  # Inside the box
goal4 = (0, 0)   # Outside

print_grid_with_path(grid4, start=start4, goal=goal4)
path4 = a_star_pathfinding(grid4, start4, goal4)

if not path4:
    print("⚠️  As expected, no path exists!")

print("\n" + "="*60)
print("✨ A* PATHFINDING DEMO COMPLETE!")
print("="*60)
