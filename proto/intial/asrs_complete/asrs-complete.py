#!/usr/bin/env python3
"""
============================================================================
PROFESSIONAL ASRS WAREHOUSE MANAGEMENT SYSTEM
Business-Grade with Realistic 3D Visualization
============================================================================
Enterprise Edition v2.0
Complete Implementation with Advanced Analytics
"""

import sys
import json
import os
import heapq
import sqlite3
import gc
from datetime import datetime, timedelta
from collections import deque
import csv

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QComboBox, QScrollArea, QHeaderView, QDialog,
    QGroupBox, QSplitter, QFrame, QTabWidget, QTextEdit, QProgressBar,
    QFileDialog, QSpinBox, QGridLayout, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QColor, QFont, QPalette, QIcon

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

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

# ============================================================================
# DATABASE FUNCTIONS (Enhanced)
# ============================================================================

def init_database():
    """Initialize enhanced database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS box_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT UNIQUE NOT NULL,
            length INTEGER NOT NULL,
            width INTEGER NOT NULL,
            category TEXT,
            weight REAL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS boxes (
            box_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            sku TEXT,
            description TEXT,
            placement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            retrieval_date TIMESTAMP,
            level INTEGER,
            status TEXT DEFAULT 'stored',
            FOREIGN KEY (model_id) REFERENCES box_models(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_id INTEGER,
            operation TEXT,
            operation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            distance_traveled REAL,
            duration REAL,
            operator TEXT,
            FOREIGN KEY (box_id) REFERENCES boxes(box_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE DEFAULT CURRENT_DATE,
            total_operations INTEGER DEFAULT 0,
            storage_operations INTEGER DEFAULT 0,
            retrieval_operations INTEGER DEFAULT 0,
            avg_distance REAL DEFAULT 0,
            peak_hour INTEGER,
            efficiency_score REAL
        )
    ''')
    
    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_boxes_status ON boxes(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_operations_date ON operations_log(operation_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_boxes_model ON boxes(model_id)')
    
    # Default models
    default_models = [
        ('Small-Box-1x1', 1, 1, 'Small', 5.0),
        ('Medium-Box-2x2', 2, 2, 'Medium', 15.0),
        ('Standard-Box-3x3', 3, 3, 'Standard', 30.0),
        ('Large-Box-4x4', 4, 4, 'Large', 50.0),
        ('Bulk-Box-5x5', 5, 5, 'Bulk', 80.0),
    ]
    
    for model_name, length, width, category, weight in default_models:
        try:
            cursor.execute('''
                INSERT INTO box_models (model_name, length, width, category, weight)
                VALUES (?, ?, ?, ?, ?)
            ''', (model_name, length, width, category, weight))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()

def get_analytics_data(days=7):
    """Get analytics data for dashboard"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Last 7 days operations
    cursor.execute('''
        SELECT DATE(operation_date), COUNT(*), AVG(distance_traveled)
        FROM operations_log
        WHERE operation_date >= datetime('now', '-7 days')
        GROUP BY DATE(operation_date)
        ORDER BY DATE(operation_date)
    ''')
    daily_ops = cursor.fetchall()
    
    # Total statistics
    cursor.execute('SELECT COUNT(*) FROM boxes WHERE status="stored"')
    total_stored = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM operations_log WHERE operation="STORED" AND DATE(operation_date) = DATE("now")')
    today_stored = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM operations_log WHERE operation="RETRIEVED" AND DATE(operation_date) = DATE("now")')
    today_retrieved = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(distance_traveled) FROM operations_log WHERE DATE(operation_date) = DATE("now")')
    avg_distance = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'daily_operations': daily_ops,
        'total_stored': total_stored,
        'today_stored': today_stored,
        'today_retrieved': today_retrieved,
        'avg_distance': round(avg_distance, 2)
    }

def export_to_csv(filename):
    """Export operations log to CSV"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT o.id, o.box_id, o.operation, o.operation_date, 
               o.distance_traveled, b.sku, bm.model_name
        FROM operations_log o
        LEFT JOIN boxes b ON o.box_id = b.box_id
        LEFT JOIN box_models bm ON b.model_id = bm.id
        ORDER BY o.operation_date DESC
    ''')
    
    data = cursor.fetchall()
    conn.close()
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Box ID', 'Operation', 'Date', 'Distance', 'SKU', 'Model'])
        writer.writerows(data)
    
    return len(data)

# ============================================================================
# CORE CLASSES
# ============================================================================

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

# ============================================================================
# PATHFINDING
# ============================================================================

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

# ============================================================================
# REALISTIC 3D WAREHOUSE VISUALIZATION
# ============================================================================

class Realistic3DViewer(QDialog):
    """Professional Realistic 3D Warehouse Rack System"""
    
    def __init__(self, rack, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏭 Warehouse 3D View - Realistic Rack System")
        self.setGeometry(50, 50, 1600, 1000)
        self.rack = rack
        self.ax = None
        self.rotation_angle = 45
        self.elevation_angle = 20
        
        # Professional dark theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['dark']};
            }}
            QLabel {{
                color: white;
            }}
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary']};
            }}
            QComboBox {{
                background-color: {COLORS['secondary']};
                color: white;
                border: 1px solid {COLORS['accent']};
                padding: 8px;
                border-radius: 4px;
            }}
        """)
        
        self.setup_ui()
        self.render_realistic_warehouse()
    
    def setup_ui(self):
        """Setup professional UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        header_layout = QVBoxLayout(header)
        
        title = QLabel("🏭 Warehouse 3D Visualization")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header_layout.addWidget(title)
        
        subtitle = QLabel(f"Realistic Rack System • {GRID_ROWS}×{GRID_COLS} Grid • {RACK_HEIGHT_LEVELS} Levels")
        subtitle.setStyleSheet("font-size: 12px; color: #E0E0E0;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Control Panel
        control_frame = QFrame()
        control_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['sidebar']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        control_layout = QHBoxLayout(control_frame)
        
        # View Controls
        view_group = QLabel("📐 View:")
        view_group.setStyleSheet("font-weight: bold; color: white; margin-right: 10px;")
        control_layout.addWidget(view_group)
        
        self.view_realistic_btn = QPushButton("🏗️ Realistic")
        self.view_realistic_btn.clicked.connect(lambda: self.change_view('realistic'))
        control_layout.addWidget(self.view_realistic_btn)
        
        self.view_top_btn = QPushButton("🔝 Top")
        self.view_top_btn.clicked.connect(lambda: self.change_view('top'))
        control_layout.addWidget(self.view_top_btn)
        
        self.view_front_btn = QPushButton("👁️ Front")
        self.view_front_btn.clicked.connect(lambda: self.change_view('front'))
        control_layout.addWidget(self.view_front_btn)
        
        self.view_aisle_btn = QPushButton("🚶 Aisle")
        self.view_aisle_btn.clicked.connect(lambda: self.change_view('aisle'))
        control_layout.addWidget(self.view_aisle_btn)
        
        control_layout.addStretch()
        
        # Render Options
        self.show_racks_check = QComboBox()
        self.show_racks_check.addItems(['Show All', 'Occupied Only', 'Empty Only'])
        self.show_racks_check.currentTextChanged.connect(lambda: self.render_realistic_warehouse())
        control_layout.addWidget(QLabel("Filter:"))
        control_layout.addWidget(self.show_racks_check)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.render_realistic_warehouse)
        control_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📸 Export")
        export_btn.clicked.connect(self.export_view)
        control_layout.addWidget(export_btn)
        
        layout.addWidget(control_frame)
        
        # 3D Canvas
        self.figure = Figure(figsize=(16, 9), dpi=100, facecolor=COLORS['dark'])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet(f"background-color: {COLORS['dark']};")
        layout.addWidget(self.canvas)
        
        # Stats Panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['sidebar']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        analytics = get_analytics_data()
        
        # Create stat cards
        stats = [
            ("📦 Total Stored", str(analytics['total_stored']), COLORS['info']),
            ("➕ Today Stored", str(analytics['today_stored']), COLORS['success']),
            ("➖ Today Retrieved", str(analytics['today_retrieved']), COLORS['warning']),
            ("📏 Avg Distance", f"{analytics['avg_distance']}m", COLORS['accent']),
            ("🏗️ Capacity", f"{self.get_capacity()}%", COLORS['danger'] if self.get_capacity() > 80 else COLORS['success'])
        ]
        
        for label_text, value_text, color in stats:
            stat_widget = QFrame()
            stat_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['secondary']};
                    border-left: 4px solid {color};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """)
            stat_layout_inner = QVBoxLayout(stat_widget)
            stat_layout_inner.setSpacing(2)
            
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 10px; color: #B0B0B0;")
            stat_layout_inner.addWidget(label)
            
            value = QLabel(value_text)
            value.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
            stat_layout_inner.addWidget(value)
            
            stats_layout.addWidget(stat_widget)
        
        layout.addWidget(stats_frame)
    
    def render_realistic_warehouse(self):
        """Render realistic 3D warehouse with vertical rack structures"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111, projection='3d', facecolor=COLORS['dark'])
        
        self.ax.set_facecolor(COLORS['dark'])
        self.figure.patch.set_facecolor(COLORS['dark'])
        
        filter_mode = self.show_racks_check.currentText()
        
        # Draw floor
        self.draw_warehouse_floor()
        
        # Draw realistic rack structures
        self.draw_rack_frames()
        
        # Draw stored boxes on shelves
        self.draw_stored_boxes(filter_mode)
        
        # Clean axes (no graph elements)
        self.clean_axes()
        
        # Set view
        self.change_view('realistic')
        
        self.canvas.draw()
    
    def draw_warehouse_floor(self):
        """Draw warehouse floor with markings"""
        # Main floor
        floor_x = [0, GRID_COLS, GRID_COLS, 0, 0]
        floor_y = [0, 0, GRID_ROWS, GRID_ROWS, 0]
        floor_z = [-0.1, -0.1, -0.1, -0.1, -0.1]
        
        vertices = [[floor_x[i], floor_y[i], floor_z[i]] for i in range(len(floor_x))]
        
        # Floor with concrete color
        floor_collection = Poly3DCollection([vertices], alpha=0.9, 
                                          facecolor=(0.25, 0.25, 0.27),
                                          edgecolor=(0.3, 0.3, 0.32), linewidth=2)
        self.ax.add_collection3d(floor_collection)
        
        # Aisle markings (yellow lines)
        for aisle in range(AISLE_COUNT):
            aisle_pos = (aisle + 0.5) * (GRID_ROWS / AISLE_COUNT)
            self.ax.plot([0, GRID_COLS], [aisle_pos, aisle_pos], [0, 0],
                        color='yellow', linewidth=2, alpha=0.6)
        
        # Grid lines (subtle)
        for i in range(0, GRID_COLS + 1, 5):
            self.ax.plot([i, i], [0, GRID_ROWS], [0, 0],
                        color='white', alpha=0.05, linewidth=0.5)
        for i in range(0, GRID_ROWS + 1, 5):
            self.ax.plot([0, GRID_COLS], [i, i], [0, 0],
                        color='white', alpha=0.05, linewidth=0.5)
    
    def draw_rack_frames(self):
        """Draw realistic rack frame structures"""
        rack_height = RACK_HEIGHT_LEVELS * 1.2
        
        for row in range(0, GRID_ROWS, 3):  # Rack every 3 rows
            for col in range(0, GRID_COLS, 5):  # Rack every 5 columns
                # Vertical posts (4 corners)
                post_positions = [
                    (col, row), (col + 0.1, row),
                    (col, row + 2.9), (col + 0.1, row + 2.9)
                ]
                
                for px, py in post_positions:
                    self.draw_rack_post(px, py, rack_height)
                
                # Horizontal beams (shelves)
                for level in range(RACK_HEIGHT_LEVELS + 1):
                    z = level * 1.2
                    self.draw_rack_beam(col, row, z, 2.9, 0.1)
    
    def draw_rack_post(self, x, y, height):
        """Draw a single vertical rack post"""
        post_width = 0.08
        
        vertices = [
            [x, y, 0], [x + post_width, y, 0],
            [x + post_width, y + post_width, 0], [x, y + post_width, 0],
            [x, y, height], [x + post_width, y, height],
            [x + post_width, y + post_width, height], [x, y + post_width, height]
        ]
        
        faces = [
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[7], vertices[6], vertices[2], vertices[3]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]],
            [vertices[4], vertices[5], vertices[6], vertices[7]]
        ]
        
        collection = Poly3DCollection(faces, alpha=0.7,
                                     facecolor=(0.4, 0.4, 0.42),
                                     edgecolor=(0.3, 0.3, 0.32), linewidth=0.5)
        self.ax.add_collection3d(collection)
    
    def draw_rack_beam(self, x, y, z, length, width):
        """Draw horizontal rack beam (shelf)"""
        beam_height = 0.05
        
        vertices = [
            [x, y, z], [x, y + length, z],
            [x + width, y + length, z], [x + width, y, z],
            [x, y, z + beam_height], [x, y + length, z + beam_height],
            [x + width, y + length, z + beam_height], [x + width, y, z + beam_height]
        ]
        
        faces = [
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[7], vertices[6], vertices[2], vertices[3]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]],
            [vertices[4], vertices[5], vertices[6], vertices[7]]
        ]
        
        collection = Poly3DCollection(faces, alpha=0.8,
                                     facecolor=(0.5, 0.5, 0.52),
                                     edgecolor=(0.4, 0.4, 0.42), linewidth=0.5)
        self.ax.add_collection3d(collection)
    
    def draw_stored_boxes(self, filter_mode):
        """Draw boxes stored on rack shelves"""
        for row in range(self.rack.rows):
            for col in range(self.rack.cols):
                cell_id = self.rack.grid[row][col]
                
                if filter_mode == 'Empty Only' and cell_id is not None:
                    continue
                if filter_mode == 'Occupied Only' and cell_id is None:
                    continue
                
                # Calculate shelf level (distribute vertically)
                level = (row % RACK_HEIGHT_LEVELS)
                z = level * 1.2 + 0.1
                
                if cell_id is not None:
                    # Occupied - draw realistic box/pallet
                    zone_color = self.get_zone_3d_color(row)
                    self.draw_realistic_box(col + 0.3, row + 0.3, z, 0.8, 0.8, 0.9, zone_color)
                    
                    # Add label
                    self.ax.text(col + 0.7, row + 0.7, z + 0.5,
                               str(cell_id), color='white', fontsize=6,
                               ha='center', va='center', weight='bold',
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor=(0.1, 0.1, 0.1, 0.7),
                                       edgecolor='none'))
                else:
                    # Empty shelf slot - draw subtle outline
                    self.draw_empty_slot(col + 0.3, row + 0.3, z, 0.8, 0.8)
    
    def draw_realistic_box(self, x, y, z, width, depth, height, color):
        """Draw a realistic 3D box/pallet"""
        vertices = [
            [x, y, z], [x + width, y, z],
            [x + width, y + depth, z], [x, y + depth, z],
            [x, y, z + height], [x + width, y, z + height],
            [x + width, y + depth, z + height], [x, y + depth, z + height]
        ]
        
        faces = [
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[7], vertices[6], vertices[2], vertices[3]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]],
            [vertices[4], vertices[5], vertices[6], vertices[7]]
        ]
        
        collection = Poly3DCollection(faces, alpha=0.85,
                                     facecolor=color,
                                     edgecolor=(0.2, 0.2, 0.25), linewidth=0.8)
        self.ax.add_collection3d(collection)
        
        # Add pallet base
        pallet_height = 0.05
        pallet_faces = [[vertices[0], vertices[1], vertices[2], vertices[3]]]
        pallet_collection = Poly3DCollection(pallet_faces, alpha=0.6,
                                            facecolor=(0.4, 0.3, 0.2),
                                            edgecolor=(0.3, 0.2, 0.1), linewidth=0.5)
        self.ax.add_collection3d(pallet_collection)
    
    def draw_empty_slot(self, x, y, z, width, depth):
        """Draw empty rack slot outline"""
        # Just draw a faint outline
        outline = [
            [x, y, z], [x + width, y, z],
            [x + width, y + depth, z], [x, y + depth, z], [x, y, z]
        ]
        
        ox = [p[0] for p in outline]
        oy = [p[1] for p in outline]
        oz = [p[2] for p in outline]
        
        self.ax.plot(ox, oy, oz, color='white', alpha=0.1, linewidth=0.3)
    
    def get_zone_3d_color(self, row):
        """Get realistic zone color"""
        for model_id, zone_info in MODEL_ZONES.items():
            zone_start, zone_end = zone_info['range']
            if zone_start <= row <= zone_end:
                return zone_info['rgb']
        return (0.5, 0.5, 0.55)
    
    def clean_axes(self):
        """Remove all graph elements"""
        self.ax.set_xlabel('')
        self.ax.set_ylabel('')
        self.ax.set_zlabel('')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_zticks([])
        self.ax.grid(False)
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        self.ax.xaxis.pane.set_edgecolor(COLORS['dark'])
        self.ax.yaxis.pane.set_edgecolor(COLORS['dark'])
        self.ax.zaxis.pane.set_edgecolor(COLORS['dark'])
        
        # Set limits
        self.ax.set_xlim(-2, GRID_COLS + 2)
        self.ax.set_ylim(-2, GRID_ROWS + 2)
        self.ax.set_zlim(0, RACK_HEIGHT_LEVELS * 1.5)
    
    def change_view(self, mode):
        """Change camera angle"""
        if not self.ax:
            return
        
        if mode == 'realistic':
            self.ax.view_init(elev=20, azim=45)
        elif mode == 'top':
            self.ax.view_init(elev=90, azim=0)
        elif mode == 'front':
            self.ax.view_init(elev=5, azim=0)
        elif mode == 'aisle':
            self.ax.view_init(elev=10, azim=90)
        
        self.canvas.draw()
    
    def export_view(self):
        """Export current view as image"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export View", "", "PNG Files (*.png);;All Files (*)"
        )
        if filename:
            self.figure.savefig(filename, dpi=300, facecolor=COLORS['dark'],
                              bbox_inches='tight')
            self.show_alert("Export Successful", f"View exported successfully to:\n{filename}", "info")
    
    def get_capacity(self):
        """Calculate capacity"""
        total = GRID_ROWS * GRID_COLS
        occupied = self.rack.get_occupied_cells()
        return int((occupied * 100) / total) if total > 0 else 0

# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

class AnalyticsDashboard(QDialog):
    """Professional Analytics Dashboard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Analytics Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['dark']};
            }}
            QLabel {{
                color: white;
            }}
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup analytics UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        
        title = QLabel("📊 Warehouse Analytics Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📥 Export CSV")
        export_btn.clicked.connect(self.export_data)
        header_layout.addWidget(export_btn)
        
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['secondary']};
                background-color: {COLORS['sidebar']};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['secondary']};
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['accent']};
            }}
        """)
        
        # Overview Tab
        overview_widget = self.create_overview_tab()
        tabs.addTab(overview_widget, "📈 Overview")
        
        # Operations Tab
        operations_widget = self.create_operations_tab()
        tabs.addTab(operations_widget, "🔄 Operations")
        
        # Efficiency Tab
        efficiency_widget = self.create_efficiency_tab()
        tabs.addTab(efficiency_widget, "⚡ Efficiency")
        
        layout.addWidget(tabs)
    
    def create_overview_tab(self):
        """Create overview analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats cards
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"background-color: {COLORS['sidebar']}; border-radius: 8px; padding: 15px;")
        stats_layout = QGridLayout(stats_frame)
        
        analytics = get_analytics_data()
        
        stats_data = [
            ("📦 Total Stored", str(analytics['total_stored']), COLORS['info']),
            ("➕ Today Stored", str(analytics['today_stored']), COLORS['success']),
            ("➖ Today Retrieved", str(analytics['today_retrieved']), COLORS['warning']),
            ("📏 Average Distance", f"{analytics['avg_distance']} m", COLORS['accent']),
        ]
        
        for i, (label_text, value_text, color) in enumerate(stats_data):
            card = self.create_stat_card(label_text, value_text, color)
            stats_layout.addWidget(card, 0, i)
        
        layout.addWidget(stats_frame)
        
        # Chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"background-color: {COLORS['sidebar']}; border-radius: 8px; padding: 15px;")
        chart_layout = QVBoxLayout(chart_frame)
        
        chart_title = QLabel("📈 Daily Operations (Last 7 Days)")
        chart_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        chart_layout.addWidget(chart_title)
        
        # Create chart
        figure = Figure(figsize=(12, 5), facecolor=COLORS['sidebar'])
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        # Plot data
        daily_ops = analytics['daily_operations']
        if daily_ops:
            dates = [op[0] for op in daily_ops]
            counts = [op[1] for op in daily_ops]
            
            ax.plot(dates, counts, marker='o', linewidth=2, markersize=8, color=COLORS['accent'])
            ax.fill_between(range(len(dates)), counts, alpha=0.3, color=COLORS['accent'])
            ax.set_facecolor(COLORS['dark'])
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel('Operations', color='white')
            ax.set_xlabel('Date', color='white')
            ax.grid(True, alpha=0.2, color='white')
            figure.tight_layout()
        
        chart_layout.addWidget(canvas)
        layout.addWidget(chart_frame)
        
        return widget
    
    def create_operations_tab(self):
        """Create operations history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Operations table
        table_frame = QFrame()
        table_frame.setStyleSheet(f"background-color: {COLORS['sidebar']}; border-radius: 8px; padding: 15px;")
        table_layout = QVBoxLayout(table_frame)
        
        table_title = QLabel("🔄 Recent Operations")
        table_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        table_layout.addWidget(table_title)
        
        # Create table
        table = QTableWidget()
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['dark']};
                color: white;
                border: none;
                gridline-color: {COLORS['secondary']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        # Load data
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.box_id, o.operation, o.operation_date, 
                   o.distance_traveled, b.sku, bm.model_name
            FROM operations_log o
            LEFT JOIN boxes b ON o.box_id = b.box_id
            LEFT JOIN box_models bm ON b.model_id = bm.id
            ORDER BY o.operation_date DESC
            LIMIT 100
        ''')
        data = cursor.fetchall()
        conn.close()
        
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['Box ID', 'Operation', 'Date', 'Distance (m)', 'SKU', 'Model'])
        table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value else '-')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)
        
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        
        table_layout.addWidget(table)
        layout.addWidget(table_frame)
        
        return widget
    
    def create_efficiency_tab(self):
        """Create efficiency metrics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        efficiency_frame = QFrame()
        efficiency_frame.setStyleSheet(f"background-color: {COLORS['sidebar']}; border-radius: 8px; padding: 15px;")
        efficiency_layout = QVBoxLayout(efficiency_frame)
        
        title = QLabel("⚡ Efficiency Metrics")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        efficiency_layout.addWidget(title)
        
        # Calculate metrics
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT AVG(distance_traveled) FROM operations_log')
        avg_dist = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM operations_log WHERE DATE(operation_date) = DATE("now")')
        today_ops = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM boxes WHERE status="stored"')
        total_stored = cursor.fetchone()[0]
        
        conn.close()
        
        capacity = int((total_stored * 100) / (GRID_ROWS * GRID_COLS))
        efficiency_score = max(0, 100 - (avg_dist * 2) - (capacity * 0.5))
        
        metrics_text = f"""
        <div style='color: white; font-size: 14px; line-height: 1.8;'>
            <p><b>📏 Average Travel Distance:</b> {avg_dist:.2f} meters</p>
            <p><b>📊 Warehouse Capacity:</b> {capacity}%</p>
            <p><b>🔄 Today's Operations:</b> {today_ops}</p>
            <p><b>⚡ Efficiency Score:</b> {efficiency_score:.1f}/100</p>
            <br>
            <p><b>Recommendations:</b></p>
            <ul>
                <li>{'✅ Excellent efficiency!' if efficiency_score > 80 else '⚠️ Consider optimizing placement strategy'}</li>
                <li>{'✅ Capacity under control' if capacity < 80 else '🔴 Warehouse nearing capacity'}</li>
                <li>{'✅ Operations running smoothly' if today_ops > 0 else '⚠️ No operations today'}</li>
            </ul>
        </div>
        """
        
        metrics_label = QLabel(metrics_text)
        metrics_label.setTextFormat(Qt.RichText)
        metrics_label.setWordWrap(True)
        efficiency_layout.addWidget(metrics_label)
        
        layout.addWidget(efficiency_frame)
        layout.addStretch()
        
        return widget
    
    def create_stat_card(self, label, value, color):
        """Create a stat card widget"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['secondary']};
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 15px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 11px; color: #B0B0B0;")
        card_layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        card_layout.addWidget(value_widget)
        
        return card
    
    def refresh_data(self):
        """Refresh all analytics data"""
        # Close and reopen
        self.close()
        dialog = AnalyticsDashboard(self.parent())
        dialog.exec()
    
    def export_data(self):
        """Export operations data to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Operations", "", "CSV Files (*.csv);;All Files (*)"
        )
        if filename:
            count = export_to_csv(filename)
            self.show_alert("Export Successful", f"Exported {count} records successfully to:\n{filename}", "info")

# ============================================================================
# ENHANCED MAIN WINDOW
# ============================================================================

class BusinessASRSindow(QMainWindow):
    """Business-Grade Main Application Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏭 Professional ASRS Warehouse Management System v2.0")

        # Initialize data
        init_database()
        self.rack = Rack(GRID_ROWS, GRID_COLS)
        self.load_state()

        # Animation and trolley state
        self.trolley_row = ORIGIN_ROW
        self.trolley_col = ORIGIN_COL
        self.trolley_path = []
        self.is_animating = False
        self.operation_mode = 'idle'
        self.pending_box_id = None
        self.pending_position = None
        self.current_view = 'grid'  # Track current view
        
        # Professional theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['dark']};
            }}
            QLabel {{
                color: white;
            }}
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary']};
            }}
            QLineEdit, QComboBox {{
                background-color: {COLORS['secondary']};
                color: white;
                border: 1px solid {COLORS['accent']};
                padding: 8px;
                border-radius: 4px;
            }}
            QTableWidget {{
                background-color: {COLORS['sidebar']};
                color: white;
                border: none;
                gridline-color: {COLORS['secondary']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            QTextEdit {{
                background-color: {COLORS['sidebar']};
                color: white;
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                padding: 8px;
            }}
            QGroupBox {{
                color: white;
                border: 2px solid {COLORS['secondary']};
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: {COLORS['secondary']};
                border-radius: 4px;
            }}
        """)

        self.setup_ui()

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_trolley)

        # Maximize window after UI setup
        self.showMaximized()
    
    def setup_ui(self):
        """Setup main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top Bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Main Content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['secondary']};
            }}
        """)
        
        # Left Panel - Controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center Panel - Visualization
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # Right Panel - Info
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 800, 450])
        
        main_layout.addWidget(splitter)
        
        # Status Bar
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"background-color: {COLORS['secondary']}; color: white; padding: 5px;")
        status_bar.showMessage("✅ System Ready")
    
    def create_top_bar(self):
        """Create top navigation bar"""
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                padding: 15px;
            }}
        """)
        layout = QHBoxLayout(top_bar)
        
        # Logo/Title
        title = QLabel("🏭 ASRS Warehouse Management System")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Quick Actions
        self.view_toggle_btn = QPushButton("🏗️ Switch to 3D View")
        self.view_toggle_btn.clicked.connect(self.toggle_view)
        layout.addWidget(self.view_toggle_btn)
        
        analytics_btn = QPushButton("📊 Analytics")
        analytics_btn.clicked.connect(self.open_analytics)
        layout.addWidget(analytics_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_state)
        layout.addWidget(save_btn)
        
        return top_bar
    
    def create_left_panel(self):
        """Create left control panel"""
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLORS['sidebar']}; padding: 15px;")
        layout = QVBoxLayout(panel)
        
        # Store Section
        store_group = QGroupBox("📦 Store Item")
        store_layout = QVBoxLayout(store_group)
        
        # Model selection
        store_layout.addWidget(QLabel("Select Model:"))
        self.model_combo = QComboBox()
        self.load_models()
        store_layout.addWidget(self.model_combo)
        
        # SKU input
        store_layout.addWidget(QLabel("SKU:"))
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Enter SKU code")
        store_layout.addWidget(self.sku_input)
        
        # Description
        store_layout.addWidget(QLabel("Description:"))
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Item description")
        store_layout.addWidget(self.desc_input)
        
        # Store button
        store_btn = QPushButton("➕ Store Item")
        store_btn.setStyleSheet(f"background-color: {COLORS['success']}; padding: 12px; font-size: 12px;")
        store_btn.clicked.connect(self.store_item)
        store_layout.addWidget(store_btn)
        
        layout.addWidget(store_group)
        
        # Retrieve Section
        retrieve_group = QGroupBox("📤 Retrieve Item")
        retrieve_layout = QVBoxLayout(retrieve_group)
        
        retrieve_layout.addWidget(QLabel("Box ID:"))
        self.retrieve_input = QLineEdit()
        self.retrieve_input.setPlaceholderText("Enter Box ID")
        retrieve_layout.addWidget(self.retrieve_input)
        
        retrieve_btn = QPushButton("➖ Retrieve Item")
        retrieve_btn.setStyleSheet(f"background-color: {COLORS['warning']}; padding: 12px; font-size: 12px;")
        retrieve_btn.clicked.connect(self.retrieve_item)
        retrieve_layout.addWidget(retrieve_btn)
        
        layout.addWidget(retrieve_group)
        
        # Quick Stats
        stats_group = QGroupBox("📊 Quick Stats")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.update_stats()
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        return panel
    
    def create_center_panel(self):
        """Create center visualization panel"""
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLORS['dark']};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        self.view_title = QLabel("🗺️ Warehouse Grid View")
        self.view_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout.addWidget(self.view_title)

        # Stacked widget for view switching
        self.view_stack = QStackedWidget()

        # Grid visualization
        self.grid_widget = self.create_grid_visualization()
        self.view_stack.addWidget(self.grid_widget)  # Index 0

        # 3D visualization
        self.view_3d_widget = self.create_3d_visualization()
        self.view_stack.addWidget(self.view_3d_widget)  # Index 1

        layout.addWidget(self.view_stack)

        return panel
    
    def create_grid_visualization(self):
        """Create 2D grid visualization"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {COLORS['dark']};")
        
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(1)
        
        cell_size = 20
        
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                cell = QLabel()
                cell.setFixedSize(cell_size, cell_size)
                cell.setAlignment(Qt.AlignCenter)
                
                # Color by zone
                zone_color = self.get_zone_color(row)
                
                if self.rack.grid[row][col] is not None:
                    cell.setStyleSheet(f"background-color: {zone_color.name()}; border: 1px solid black;")
                    cell.setToolTip(f"Box ID: {self.rack.grid[row][col]}")
                else:
                    cell.setStyleSheet(f"background-color: {COLORS['secondary']}; border: 1px solid {COLORS['dark']};")
                    cell.setToolTip(f"Empty ({row}, {col})")
                
                grid_layout.addWidget(cell, row, col)
        
        scroll.setWidget(grid_container)
        return scroll
    
    def create_right_panel(self):
        """Create right info panel"""
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLORS['sidebar']}; padding: 15px;")
        layout = QVBoxLayout(panel)
        
        # Operations Log
        log_group = QGroupBox("📋 Operations Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(300)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        # Inventory Table
        inventory_group = QGroupBox("📦 Current Inventory")
        inventory_layout = QVBoxLayout(inventory_group)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(4)
        self.inventory_table.setHorizontalHeaderLabels(['Box ID', 'SKU', 'Model', 'Date'])
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.update_inventory_table()
        inventory_layout.addWidget(self.inventory_table)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.update_inventory_table)
        inventory_layout.addWidget(refresh_btn)
        
        layout.addWidget(inventory_group)
        
        return panel
    
    def load_models(self):
        """Load box models from database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, model_name, length, width FROM box_models')
        models = cursor.fetchall()
        conn.close()
        
        self.model_combo.clear()
        for model_id, name, length, width in models:
            self.model_combo.addItem(f"{name} ({length}×{width})", model_id)
    
    def store_item(self):
        """Store item in warehouse"""
        model_id = self.model_combo.currentData()
        sku = self.sku_input.text().strip()
        description = self.desc_input.text().strip()
        
        if not sku:
            self.show_alert("Missing SKU", "Please enter a SKU (Stock Keeping Unit) for the item.", "warning")
            return
        
        # Get model info
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT length, width FROM box_models WHERE id=?', (model_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            self.show_alert("Model Not Found", "The selected model was not found in the system.\n\nPlease select a valid model.", "error")
            return
        
        length, width = result
        size = max(length, width)
        
        # Find slot
        slot = self.rack.find_nearest_empty_slot(size, ORIGIN_ROW, ORIGIN_COL)
        
        if not slot:
            conn.close()
            self.show_alert("No Available Slot", "No available storage slot found for this item.\n\nThe warehouse may be full or the designated zone is at capacity.", "warning")
            return
        
        # Store in database
        cursor.execute('''
            INSERT INTO boxes (model_id, sku, description, level, status)
            VALUES (?, ?, ?, ?, 'stored')
        ''', (model_id, sku, description, slot[0] % RACK_HEIGHT_LEVELS))
        box_id = cursor.lastrowid
        
        # Calculate distance
        distance = calculate_distance((ORIGIN_ROW, ORIGIN_COL), slot)
        
        # Log operation
        cursor.execute('''
            INSERT INTO operations_log (box_id, operation, distance_traveled)
            VALUES (?, 'STORED', ?)
        ''', (box_id, distance))
        
        conn.commit()
        conn.close()
        
        # Update rack
        self.rack.place_box(box_id, slot[0], slot[1], size)
        
        # UI updates
        self.log_text.append(f"✅ Stored Box #{box_id} (SKU: {sku}) at ({slot[0]}, {slot[1]}) - Distance: {distance}m")
        self.sku_input.clear()
        self.desc_input.clear()
        self.update_stats()
        self.update_inventory_table()
        self.refresh_grid()
        
        self.show_alert("Storage Successful", f"Item stored successfully!\n\nBox ID: {box_id}\nLocation: Row {slot[0]}, Column {slot[1]}", "info")
    
    def retrieve_item(self):
        """Retrieve item from warehouse"""
        if self.is_animating:
            self.show_alert("Operation in Progress", "Please wait for the current operation to complete.", "warning")
            return

        box_id_text = self.retrieve_input.text().strip()
        
        if not box_id_text:
            self.show_alert("Missing Box ID", "Please enter a Box ID for retrieval.", "warning")
            return
        
        try:
            box_id = int(box_id_text)
        except ValueError:
            self.show_alert("Invalid Box ID", "Please enter a valid numeric Box ID.", "error")
            return
        
        if box_id not in self.rack.box_locations:
            self.show_alert("Box Not Found", "The specified box was not found in the warehouse.\n\nPlease check the Box ID and try again.", "error")
            return
        
        # Get location
        row, col, size = self.rack.box_locations[box_id]
        
        # Animate trolley
        path, _ = a_star_path((ORIGIN_ROW, ORIGIN_COL), (row, col), self.rack)
        return_path, _ = a_star_path((row, col), (ORIGIN_ROW, ORIGIN_COL), self.rack)
        self.trolley_path = path + return_path
        self.pending_box_id = box_id
        self.operation_mode = 'retrieving'
        
        self.animation_timer.start(100) # ms for each step
        self.is_animating = True

    def complete_operation(self):
        """Complete the operation after animation."""
        if self.operation_mode == 'storing':
            # Finish storing
            box_id = self.pending_box_id
            slot = self.pending_position
            size = self.pending_size
            # Update rack
            self.rack.place_box(box_id, slot[0], slot[1], size)
            # UI updates
            self.log_text.append(f"✅ Stored Box #{box_id} at ({slot[0]}, {slot[1]})")
            self.desc_input.clear()
            self.update_stats()
            self.update_inventory_table()
            self.refresh_grid()
            self.show_alert("Storage Successful", f"Item stored successfully!\n\nBox ID: {box_id}\nLocation: Row {slot[0]}, Column {slot[1]}", "info")
        elif self.operation_mode == 'retrieving':
            # Finish retrieving
            box_id = self.pending_box_id
            row, col, size = self.rack.box_locations[box_id]
            distance = calculate_distance((row, col), (ORIGIN_ROW, ORIGIN_COL))
            # Remove from rack
            self.rack.remove_box(box_id)
            # Update database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('UPDATE boxes SET status="retrieved", retrieval_date=CURRENT_TIMESTAMP WHERE box_id=?', (box_id,))
            cursor.execute('''
                INSERT INTO operations_log (box_id, operation, distance_traveled)
                VALUES (?, 'RETRIEVED', ?)
            ''', (box_id, distance))
            conn.commit()
            conn.close()
            # UI updates
            self.log_text.append(f"✅ Retrieved Box #{box_id} from ({row}, {col}) - Distance: {distance}m")
            self.retrieve_input.clear()
            self.update_stats()
            self.update_inventory_table()
            self.refresh_grid()
            self.show_alert("Retrieval Successful", f"Item retrieved successfully!\n\nDistance traveled: {distance} units", "info")
    
    def update_stats(self):
        """Update statistics display"""
        analytics = get_analytics_data()
        capacity = int((analytics['total_stored'] * 100) / (GRID_ROWS * GRID_COLS))
        
        stats_html = f"""
        <div style='color: white; line-height: 1.6;'>
            <p><b>📦 Total Stored:</b> {analytics['total_stored']}</p>
            <p><b>➕ Today Stored:</b> {analytics['today_stored']}</p>
            <p><b>➖ Today Retrieved:</b> {analytics['today_retrieved']}</p>
            <p><b>📏 Avg Distance:</b> {analytics['avg_distance']}m</p>
            <p><b>🏗️ Capacity:</b> {capacity}%</p>
        </div>
        """
        self.stats_label.setText(stats_html)
    
    def update_inventory_table(self):
        """Update inventory table"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.box_id, b.sku, bm.model_name, b.placement_date
            FROM boxes b
            JOIN box_models bm ON b.model_id = bm.id
            WHERE b.status = 'stored'
            ORDER BY b.placement_date DESC
        ''')
        data = cursor.fetchall()
        conn.close()
        
        self.inventory_table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.inventory_table.setItem(row_idx, col_idx, item)
    
    def refresh_grid(self):
        """Refresh grid visualization"""
        # Recreate center panel
        old_center = self.centralWidget().layout().itemAt(1).widget().widget(1)
        new_center = self.create_center_panel()
        
        splitter = self.centralWidget().layout().itemAt(1).widget()
        splitter.replaceWidget(1, new_center)
        old_center.deleteLater()
    
    def get_zone_color(self, row):
        """Get zone color for row"""
        for model_id, zone_info in MODEL_ZONES.items():
            zone_start, zone_end = zone_info['range']
            if zone_start <= row <= zone_end:
                return zone_info['color']
        return QColor(COLORS['secondary'])
    
    def create_3d_visualization(self):
        """Create embedded 3D visualization"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create 3D canvas
        self.figure_3d = Figure(figsize=(12, 8), dpi=100, facecolor=COLORS['dark'])
        self.canvas_3d = FigureCanvas(self.figure_3d)
        self.canvas_3d.setStyleSheet(f"background-color: {COLORS['dark']};")
        layout.addWidget(self.canvas_3d)

        # 3D view controls
        controls = QFrame()
        controls.setStyleSheet(f"background-color: {COLORS['secondary']}; border-radius: 3px; padding: 5px;")
        controls_layout = QHBoxLayout(controls)

        label = QLabel("3D View Controls:")
        label.setStyleSheet("color: white; font-weight: bold;")
        controls_layout.addWidget(label)

        btn_3d = QPushButton("🎨 3D Perspective")
        btn_3d.setStyleSheet(f"background-color: {COLORS['accent']};")
        btn_3d.clicked.connect(lambda: self.change_3d_view('3d'))
        controls_layout.addWidget(btn_3d)

        btn_top = QPushButton("🔝 Top View")
        btn_top.clicked.connect(lambda: self.change_3d_view('top'))
        controls_layout.addWidget(btn_top)

        btn_front = QPushButton("👁️ Front View")
        btn_front.clicked.connect(lambda: self.change_3d_view('front'))
        controls_layout.addWidget(btn_front)

        btn_side = QPushButton("↔️ Side View")
        btn_side.clicked.connect(lambda: self.change_3d_view('side'))
        controls_layout.addWidget(btn_side)

        controls_layout.addStretch()
        layout.addWidget(controls)

        return widget

    def toggle_view(self):
        """Toggle between grid and 3D views"""
        if self.current_view == 'grid':
            # Switch to 3D
            self.current_view = '3d'
            self.view_stack.setCurrentIndex(1)
            self.view_title.setText("🏗️ Warehouse 3D Visualization")
            self.view_toggle_btn.setText("🗺️ Switch to Grid View")
            self.render_3d()
        else:
            # Switch to grid
            self.current_view = 'grid'
            self.view_stack.setCurrentIndex(0)
            self.view_title.setText("🗺️ Warehouse Grid View")
            self.view_toggle_btn.setText("🏗️ Switch to 3D View")
            self.refresh_grid()

    def change_3d_view(self, view_type):
        """Change 3D view perspective"""
        if not hasattr(self, 'ax_3d') or self.ax_3d is None:
            return

        if view_type == 'top':
            self.ax_3d.view_init(elev=90, azim=-90)
        elif view_type == 'front':
            self.ax_3d.view_init(elev=0, azim=-90)
        elif view_type == 'side':
            self.ax_3d.view_init(elev=0, azim=0)
        else:  # 3D perspective
            self.ax_3d.view_init(elev=25, azim=45)

        self.canvas_3d.draw()

    def render_3d(self):
        """Render 3D warehouse visualization"""
        self.figure_3d.clear()
        self.ax_3d = self.figure_3d.add_subplot(111, projection='3d', facecolor=COLORS['dark'])

        # Draw boxes
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if self.rack.grid[row][col] is not None:
                    zone_color = self.get_zone_3d_color(row)
                    self.draw_3d_box(self.ax_3d, col, row, 0, 1, 1, 1, zone_color, alpha=0.7)

        # Draw trolley
        self.draw_3d_box(self.ax_3d, self.trolley_col, self.trolley_row, 0, 1, 1, 1.5,
                        (1.0, 0.5, 0.0), alpha=0.9)

        # Styling
        self.ax_3d.set_xlabel('Columns', color='white', fontsize=10)
        self.ax_3d.set_ylabel('Levels', color='white', fontsize=10)
        self.ax_3d.set_zlabel('Height', color='white', fontsize=10)
        self.ax_3d.set_title('3D Warehouse View', color='white', fontsize=12, pad=20)

        self.ax_3d.set_xlim(0, GRID_COLS)
        self.ax_3d.set_ylim(0, GRID_ROWS)
        self.ax_3d.set_zlim(0, 10)

        self.ax_3d.tick_params(colors='white', labelsize=8)
        self.ax_3d.xaxis.pane.fill = False
        self.ax_3d.yaxis.pane.fill = False
        self.ax_3d.zaxis.pane.fill = False
        self.ax_3d.grid(True, alpha=0.3, color='white')

        self.ax_3d.view_init(elev=25, azim=45)
        self.canvas_3d.draw()

    def draw_3d_box(self, ax, x, y, z, dx, dy, dz, color, alpha=0.7):
        """Draw a 3D box"""
        xx = [x, x, x+dx, x+dx, x, x, x+dx, x+dx]
        yy = [y, y+dy, y+dy, y, y, y+dy, y+dy, y]
        zz = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]

        vertices = [[xx[i], yy[i], zz[i]] for i in range(8)]

        faces = [[vertices[0], vertices[1], vertices[5], vertices[4]],
                [vertices[7], vertices[6], vertices[2], vertices[3]],
                [vertices[0], vertices[3], vertices[2], vertices[1]],
                [vertices[4], vertices[5], vertices[6], vertices[7]],
                [vertices[0], vertices[4], vertices[7], vertices[3]],
                [vertices[1], vertices[2], vertices[6], vertices[5]]]

        collection = Poly3DCollection(faces, alpha=alpha, facecolor=color,
                                     edgecolor='white', linewidths=0.5)
        ax.add_collection3d(collection)

    def get_zone_3d_color(self, row):
        """Get zone RGB color for 3D rendering"""
        for model_id, zone_info in MODEL_ZONES.items():
            zone_start, zone_end = zone_info['range']
            if zone_start <= row <= zone_end:
                color = zone_info['color']
                return (color.redF(), color.greenF(), color.blueF())
        return (0.5, 0.5, 0.5)

    def show_alert(self, title, message, icon_type="info"):
        """Show styled alert message box"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if icon_type == "info":
            msg_box.setIcon(QMessageBox.Information)
        elif icon_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif icon_type == "error":
            msg_box.setIcon(QMessageBox.Critical)
        elif icon_type == "question":
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['sidebar']};
            }}
            QMessageBox QLabel {{
                color: white;
                font-size: 12px;
                padding: 10px;
                min-width: 300px;
            }}
            QMessageBox QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)

        if icon_type == "question":
            return msg_box.exec() == QMessageBox.Yes
        else:
            msg_box.exec()
            return None

    def animate_trolley(self):
        """Animate trolley movement"""
        if self.trolley_path:
            next_row, next_col = self.trolley_path.pop(0)
            self.trolley_row = next_row
            self.trolley_col = next_col
            self.refresh_grid()

            if self.current_view == '3d':
                self.render_3d()
        else:
            self.animation_timer.stop()
            self.is_animating = False
            self.operation_mode = 'idle'
            self.statusBar().showMessage("✅ Operation Complete", 3000)

    def open_3d_viewer(self):
        """Open 3D warehouse viewer in dialog"""
        dialog = Realistic3DViewer(self.rack, self)
        dialog.exec()
    
    def open_analytics(self):
        """Open analytics dashboard"""
        dialog = AnalyticsDashboard(self)
        dialog.exec()
    
    def save_state(self):
        """Save warehouse state"""
        state = {
            'box_locations': self.rack.box_locations,
            'grid': [[cell for cell in row] for row in self.rack.grid]
        }
        
        with open(SAVE_FILE, 'w') as f:
            json.dump(state, f)
        
        self.statusBar().showMessage("✅ State saved successfully", 3000)
        self.show_alert("Save Successful", "Warehouse state has been saved successfully!", "info")
    
    def load_state(self):
        """Load warehouse state"""
        if not os.path.exists(SAVE_FILE):
            return
        
        try:
            with open(SAVE_FILE, 'r') as f:
                state = json.load(f)
            
            self.rack.box_locations = {int(k): tuple(v) for k, v in state['box_locations'].items()}
            self.rack.grid = state['grid']
            
        except Exception as e:
            print(f"Error loading state: {e}")
    
    def closeEvent(self, event):
        """Handle window close"""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Save warehouse state before exiting?',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            self.save_state()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("ASRS Warehouse Management System")
    app.setOrganizationName("Professional Warehouse Solutions")
    app.setApplicationVersion("2.0")
    
    # Create and show main window
    window = BusinessASRSMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
