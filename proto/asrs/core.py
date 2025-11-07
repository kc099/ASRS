"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - CORE CLASSES
============================================================================
"""

from collections import deque
from .config import MODEL_ZONES

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
        """Find nearest empty slot within the designated zone using BFS."""
        if model_size not in MODEL_ZONES:
            return None # No zone defined for this model size

        zone_info = MODEL_ZONES[model_size]
        start_row, end_row = zone_info['range']

        # Iterate through the zone to find the first available slot
        for r in range(start_row, end_row + 1):
            for c in range(self.cols):
                if self._can_fit(r, c, model_size):
                    return (r, c)
        
        return None
    
    def _can_fit(self, row, col, size):
        """Check if box can fit at position"""
        # Check if the box would go out of bounds (both grid and zone)
        if row + size > self.rows or col + size > self.cols:
            return False
        
        # Check if the box stays within its designated zone
        for r_check in range(row, row + size):
            found_zone = False
            for zone in MODEL_ZONES.values():
                if zone['range'][0] <= r_check <= zone['range'][1]:
                    # This part of the box is in a valid zone.
                    # Now, ensure it's the *correct* zone for this size.
                    if MODEL_ZONES[size]['range'][0] <= r_check <= MODEL_ZONES[size]['range'][1]:
                        found_zone = True
                        break
            if not found_zone:
                return False # Part of the box is outside its designated zone

        # Check if the area is occupied
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
