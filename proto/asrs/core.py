"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - CORE CLASSES
============================================================================
"""

from collections import deque

class Box:
    """Box/Item model"""
    def __init__(self, model_id, length, width, box_id=None, sku=None, description=None):
        self.box_id = box_id
        self.model_id = model_id
        self.length = length
        self.width = width
        self.sku = sku
        self.description = description

class Rack:
    """Enhanced Rack system"""
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.box_locations = {}
        
    def find_nearest_empty_slot(self, model_size, origin_row, origin_col):
        """Find nearest empty slot using optimized search"""
        visited = set()
        queue = deque([(origin_row, origin_col, 0)])
        
        while queue:
            row, col, dist = queue.popleft()
            
            if (row, col) in visited:
                continue
            visited.add((row, col))
            
            # Check if slot fits the box
            if self._can_fit(row, col, model_size):
                return (row, col)
            
            # Explore neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                    queue.append((new_row, new_col, dist + 1))
        
        return None
    
    def _can_fit(self, row, col, size):
        """Check if box can fit at position"""
        if row + size > self.rows or col + size > self.cols:
            return False
        
        for r in range(row, row + size):
            for c in range(col, col + size):
                if self.grid[r][c] is not None:
                    return False
        return True
    
    def place_box(self, box_id, row, col, size):
        """Place box on rack"""
        for r in range(row, row + size):
            for c in range(col, col + size):
                self.grid[r][c] = box_id
        self.box_locations[box_id] = (row, col, size)
    
    def remove_box(self, box_id):
        """Remove box from rack"""
        if box_id not in self.box_locations:
            return False
        
        row, col, size = self.box_locations[box_id]
        for r in range(row, row + size):
            for c in range(col, col + size):
                self.grid[r][c] = None
        
        del self.box_locations[box_id]
        return True
    
    def get_occupied_cells(self):
        """Count occupied cells"""
        count = 0
        for row in self.grid:
            for cell in row:
                if cell is not None:
                    count += 1
        return count
