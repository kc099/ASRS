"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - MAIN APPLICATION WINDOW
============================================================================
"""

import json
import os
import sqlite3



from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLineEdit, QLabel, QMessageBox, 
    QComboBox, QScrollArea, QGroupBox, QSplitter, QFrame, QTextEdit, 
    QStackedWidget, QGridLayout, QApplication, QFormLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap

from ..config import (
    DATABASE, SAVE_FILE, GRID_ROWS, GRID_COLS, RACK_HEIGHT_LEVELS, 
    ORIGIN_ROW, ORIGIN_COL, MODEL_ZONES, COLORS
)
from ..database import init_database, get_analytics_data
from ..core import Rack
from ..pathfinding import calculate_distance
from ..visualization import Realistic3DViewer
from .analytics_dashboard import AnalyticsDashboard

class BusinessASRSMainWindow(QMainWindow):
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
        self.grid_cells = []
        
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

        # Set responsive window size and center it
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen_geometry.width() * 0.9), int(screen_geometry.height() * 0.9))
        self.move(screen_geometry.center() - self.rect().center())

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
                padding: 10px;
            }}
        """)
        layout = QHBoxLayout(top_bar)
        layout.setSpacing(10)

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap('logo.png')
        logo_label.setPixmap(pixmap.scaledToHeight(40, Qt.SmoothTransformation))
        layout.addWidget(logo_label)
        
        # Logo/Title
        title = QLabel("ASRS Warehouse Management System")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # View Buttons
        self.grid_view_btn = QPushButton("🗺️ Grid View")
        self.grid_view_btn.clicked.connect(self.show_grid_view)
        layout.addWidget(self.grid_view_btn)

        self.threed_view_btn = QPushButton("🏗️ 3D View")
        self.threed_view_btn.clicked.connect(self.show_3d_view)
        layout.addWidget(self.threed_view_btn)

        fullscreen_btn = QPushButton("🖥️ Toggle Fullscreen")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(fullscreen_btn)
        
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

        # Stacked widget for view switching
        self.view_stack = QStackedWidget()

        # Grid visualization
        self.grid_widget = self.create_grid_visualization()
        self.view_stack.addWidget(self.grid_widget)  # Index 0

        # 3D visualization
        self.view_3d_widget = Realistic3DViewer(self.rack)
        self.view_stack.addWidget(self.view_3d_widget)  # Index 1

        layout.addWidget(self.view_stack)

        return panel
    
    def create_grid_visualization(self):
        """Create 2D grid visualization with zone labels."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setStyleSheet(f"background-color: {COLORS['dark']};")
        
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(1)
        
        cell_size = 18
        
        # Add zone labels to the first column
        for zone_id, zone_info in MODEL_ZONES.items():
            start_row, end_row = zone_info['range']
            row_span = end_row - start_row + 1
            
            zone_label = QLabel(zone_info['name'])
            zone_label.setAlignment(Qt.AlignCenter)
            zone_label.setStyleSheet(f"""
                background-color: {zone_info['color'].darker(150).name()};
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
            """)
            grid_layout.addWidget(zone_label, start_row, 0, row_span, 1)

        self.grid_cells = []
        for row in range(GRID_ROWS):
            row_cells = []
            # Start grid cells from column 1
            for col in range(GRID_COLS):
                cell = QLabel()
                cell.setFixedSize(cell_size, cell_size)
                cell.setAlignment(Qt.AlignCenter)
                
                grid_layout.addWidget(cell, row, col + 1)
                row_cells.append(cell)
            self.grid_cells.append(row_cells)
        
        self.refresh_grid() # Initial population of grid
        
        scroll.setWidget(grid_container)
        return scroll
    
    def create_right_panel(self):
        """Create right info panel"""
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {COLORS['sidebar']}; padding: 15px;")
        layout = QVBoxLayout(panel)
        
        # Zone Legend
        legend_group = QGroupBox("🗺️ Zone Legend")
        legend_layout = QFormLayout(legend_group)
        legend_layout.setSpacing(10)

        for zone_id, zone_info in MODEL_ZONES.items():
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f"background-color: {zone_info['color'].name()}; border-radius: 3px;")
            legend_layout.addRow(color_label, QLabel(zone_info['name']))

        empty_label = QLabel()
        empty_label.setFixedSize(20, 20)
        empty_label.setStyleSheet(f"background-color: {COLORS['danger']}; border-radius: 3px;")
        legend_layout.addRow(empty_label, QLabel("Empty Slot"))

        layout.addWidget(legend_group)

        # Operations Log
        log_group = QGroupBox("📋 Operations Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(250)
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
        """Refresh grid visualization by updating existing cells."""
        if not self.grid_cells:
            return

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                cell = self.grid_cells[row][col]
                zone_color = self.get_zone_color(row)
                
                if self.rack.grid[row][col] is not None:
                    cell.setStyleSheet(f"background-color: {zone_color.name()}; border: 1px solid black;")
                    cell.setToolTip(f"Box ID: {self.rack.grid[row][col]}")
                else:
                    cell.setStyleSheet(f"background-color: {COLORS['danger']}; border: 1px solid {COLORS['dark']};")
                    cell.setToolTip(f"Empty ({row}, {col})")
    
    def get_zone_color(self, row):
        """Get zone color for row"""
        for model_id, zone_info in MODEL_ZONES.items():
            zone_start, zone_end = zone_info['range']
            if zone_start <= row <= zone_end:
                return zone_info['color']
        return QColor(COLORS['secondary'])

    def show_grid_view(self):
        """Switch to the grid view."""
        self.view_stack.setCurrentIndex(0)

    def show_3d_view(self):
        """Switch to the 3D view."""
        self.view_3d_widget.render_realistic_warehouse() # Refresh the view
        self.view_stack.setCurrentIndex(1)

    def toggle_fullscreen(self):
        """Toggle between maximized and normal window state."""
        print("Toggle fullscreen button clicked.")
        if self.isMaximized():
            print("Switching to normal state.")
            self.showNormal()
        else:
            print("Switching to maximized state.")
            self.showMaximized()

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
        if icon_type == "question":
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

        # Set word wrap on the label programmatically
        try:
            label = msg_box.findChild(QLabel, "qt_msgbox_label")
            if label:
                label.setWordWrap(True)
        except Exception:
            pass # Failsafe if the label name changes in future Qt versions

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

            if self.view_stack.currentIndex() == 1: # If 3D view is active
                self.view_3d_widget.render_realistic_warehouse()
        else:
            self.animation_timer.stop()
            self.is_animating = False
            self.operation_mode = 'idle'
            self.statusBar().showMessage("✅ Operation Complete", 3000)

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
        if self.show_alert(
            'Confirm Exit',
            'Save warehouse state before exiting?',
            icon_type="question"
        ):
            self.save_state()
            event.accept()
        else:
            event.ignore()
