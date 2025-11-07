"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - CONFIGURATION
============================================================================
"""

from PySide6.QtGui import QColor

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE = "asrs_business.db"
SAVE_FILE = "asrs_business_state.json"

GRID_ROWS = 30
GRID_COLS = 25
RACK_HEIGHT_LEVELS = 6  # Number of vertical levels in rack
AISLE_COUNT = 2  # Number of aisles
ORIGIN_ROW = GRID_ROWS - 1
ORIGIN_COL = 0

MODEL_ZONES = {
    1: {'range': (0, 3), 'name': 'Zone-A: Small Items', 'color': QColor(100, 180, 255), 'rgb': (0.4, 0.7, 1.0)},
    2: {'range': (4, 9), 'name': 'Zone-B: Medium Items', 'color': QColor(100, 220, 150), 'rgb': (0.4, 0.86, 0.6)},
    3: {'range': (10, 15), 'name': 'Zone-C: Standard Items', 'color': QColor(255, 200, 100), 'rgb': (1.0, 0.78, 0.4)},
    4: {'range': (16, 21), 'name': 'Zone-D: Large Items', 'color': QColor(255, 150, 100), 'rgb': (1.0, 0.6, 0.4)},
    5: {'range': (22, 29), 'name': 'Zone-E: Bulk Items', 'color': QColor(220, 120, 180), 'rgb': (0.86, 0.47, 0.7)},
}

# Professional color scheme
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#34495E', 
    'accent': '#3498DB',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'info': '#16A085',
    'light': '#ECF0F1',
    'dark': '#1A252F',
    'sidebar': '#1E2A36',
}
