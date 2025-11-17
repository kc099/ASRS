"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - PATHFINDING
============================================================================
"""

import heapq

def calculate_distance(start, end):
    """Manhattan distance"""
    return abs(start[0] - end[0]) + abs(start[1] - end[1])

def a_star_path(start, end, rack):
    """A* pathfinding"""
    def heuristic(pos):
        return calculate_distance(pos, end)
    
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start), 0, start, [start]))
    visited = set()
    
    while open_set:
        _, cost, current, path = heapq.heappop(open_set)
        
        if current == end:
            return path, cost
        
        if current in visited:
            continue
        visited.add(current)
        
        # Explore neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row = current[0] + dr
            new_col = current[1] + dc
            
            if 0 <= new_row < rack.rows and 0 <= new_col < rack.cols:
                neighbor = (new_row, new_col)
                new_cost = cost + 1
                priority = new_cost + heuristic(neighbor)
                heapq.heappush(open_set, (priority, new_cost, neighbor, path + [neighbor]))
    
    return [], float('inf')
