import sys
import json
import os
import heapq
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTableWidget, QTableWidgetItem, 
                               QPushButton, QLineEdit, QLabel, QMessageBox, 
                               QComboBox, QGroupBox, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

# Save file
SAVE_FILE = "asrs_state.json"

# Grid dimensions
GRID_ROWS = 20
GRID_COLS = 20

# Origin point (bottom-left corner)
ORIGIN_ROW = GRID_ROWS - 1
ORIGIN_COL = 0

# Colors
EMPTY_COLOR = QColor(240, 240, 240)
OCCUPIED_COLOR = QColor(34, 139, 34)
TROLLEY_COLOR = QColor(220, 20, 60)
PLACING_COLOR = QColor(255, 215, 0)
PATH_COLOR = QColor(173, 216, 230)
RETRIEVING_COLOR = QColor(255, 165, 0)

# ==================== DATA STRUCTURES ====================

class Box:
    """Represents a box to be stored"""
    def __init__(self, length, width, box_id=None):
        self.length = length
        self.width = width
        self.box_id = box_id
    
    def to_dict(self):
        return {'length': self.length, 'width': self.width, 'box_id': self.box_id}
    
    @staticmethod
    def from_dict(data):
        return Box(data['length'], data['width'], data['box_id'])

class Rack:
    """Represents the ASRS rack system"""
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.boxes = {}
        self.box_positions = {}
        self.next_box_id = 1
        self.box_order = []
    
    def can_place_box(self, box, start_row, start_col):
        end_row = start_row + box.width
        end_col = start_col + box.length
        
        if end_row > self.rows or end_col > self.cols:
            return False
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                if self.grid[r][c] is not None:
                    return False
        
        return True
    
    def place_box(self, box, start_row, start_col):
        if not self.can_place_box(box, start_row, start_col):
            return False
        
        box.box_id = self.next_box_id
        self.next_box_id += 1
        
        end_row = start_row + box.width
        end_col = start_col + box.length
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                self.grid[r][c] = box.box_id
        
        self.boxes[box.box_id] = box
        self.box_positions[box.box_id] = (start_row, start_col)
        self.box_order.append(box.box_id)
        
        return True
    
    def remove_box(self, box_id):
        if box_id not in self.boxes:
            return False
        
        start_row, start_col = self.box_positions[box_id]
        box = self.boxes[box_id]
        
        end_row = start_row + box.width
        end_col = start_col + box.length
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                self.grid[r][c] = None
        
        del self.boxes[box_id]
        del self.box_positions[box_id]
        self.box_order.remove(box_id)
        
        return True
    
    def get_lifo_box(self):
        if not self.box_order:
            return None
        return self.box_order[-1]
    
    def get_fifo_box(self):
        if not self.box_order:
            return None
        return self.box_order[0]
    
    def find_closest_available_location(self, box, origin_row, origin_col):
        closest_location = None
        min_distance = float('inf')
        
        for row in range(self.rows - box.width + 1):
            for col in range(self.cols - box.length + 1):
                if self.can_place_box(box, row, col):
                    distance = math.sqrt((row - origin_row)**2 + (col - origin_col)**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_location = (row, col)
        
        return closest_location
    
    def get_occupied_cells(self):
        return sum(1 for row in self.grid for cell in row if cell is not None)
    
    def to_dict(self):
        return {
            'rows': self.rows,
            'cols': self.cols,
            'grid': self.grid,
            'boxes': {box_id: box.to_dict() for box_id, box in self.boxes.items()},
            'box_positions': self.box_positions,
            'next_box_id': self.next_box_id,
            'box_order': self.box_order
        }
    
    @staticmethod
    def from_dict(data):
        rack = Rack(data['rows'], data['cols'])
        rack.grid = data['grid']
        rack.boxes = {int(box_id): Box.from_dict(box_data) 
                     for box_id, box_data in data['boxes'].items()}
        rack.box_positions = {int(k): tuple(v) for k, v in data['box_positions'].items()}
        rack.next_box_id = data['next_box_id']
        rack.box_order = data.get('box_order', [])
        return rack

# ==================== A* PATHFINDING ====================

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_pathfinding(grid, start, goal):
    rows = len(grid)
    cols = len(grid[0])
    
    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_list:
        current = heapq.heappop(open_list)[1]
        
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path[1:]
        
        neighbors = [
            (current[0]-1, current[1]),
            (current[0]+1, current[1]),
            (current[0], current[1]-1),
            (current[0], current[1]+1)
        ]
        
        for neighbor in neighbors:
            row, col = neighbor
            
            if not (0 <= row < rows and 0 <= col < cols):
                continue
            
            tentative_g = g_score[current] + 1
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_list, (f_score[neighbor], neighbor))
    
    return []

# ==================== SAVE/LOAD ====================

def save_game_state(rack):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(rack.to_dict(), f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

def load_game_state():
    if not os.path.exists(SAVE_FILE):
        return None
    
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        return Rack.from_dict(data)
    except Exception as e:
        print(f"Error loading: {e}")
        return None

# ==================== MAIN WINDOW ====================

class ASRSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASRS - Storage & Retrieval with LIFO/FIFO")
        self.setGeometry(100, 100, 900, 850)
        self.setMinimumSize(850, 800)
        
        self.rack = load_game_state()
        if self.rack is None:
            self.rack = Rack(GRID_ROWS, GRID_COLS)
        
        self.trolley_row = ORIGIN_ROW
        self.trolley_col = ORIGIN_COL
        self.trolley_path = []
        self.is_animating = False
        self.operation_mode = 'idle'
        self.animation_cell_index = 0
        self.animation_cells = []
        self.pending_box = None
        self.pending_position = None
        self.path_visualization = []
        self.retrieving_box_id = None
        
        self.setup_ui()
        self.update_grid_display()
        self.update_stats()
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 8, 10, 8)
        
        # Title
        title = QLabel("ASRS - Storage & Retrieval System (LIFO/FIFO)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Info
        info_label = QLabel("📍 Origin: (19,0) | 🎯 Closest location | 🚛 A* pathfinding | 📦 LIFO/FIFO retrieval")
        info_label.setStyleSheet("padding: 4px; background-color: #e8f5e9; font-size: 10px;")
        main_layout.addWidget(info_label)
        
        # Operations
        operations_layout = QHBoxLayout()
        
        # Storage
        storage_group = QGroupBox("📦 Storage")
        storage_layout = QHBoxLayout()
        storage_layout.addWidget(QLabel("L:"))
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("1-20")
        self.length_input.setMaximumWidth(50)
        storage_layout.addWidget(self.length_input)
        
        storage_layout.addWidget(QLabel("W:"))
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("1-20")
        self.width_input.setMaximumWidth(50)
        storage_layout.addWidget(self.width_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_box)
        storage_layout.addWidget(self.add_button)
        storage_group.setLayout(storage_layout)
        operations_layout.addWidget(storage_group)
        
        # Retrieval
        retrieval_group = QGroupBox("🔄 Retrieval")
        retrieval_layout = QHBoxLayout()
        self.retrieval_mode = QComboBox()
        self.retrieval_mode.addItems(['LIFO', 'FIFO' ,'BY ID'])
        self.retrieval_mode.setMaximumWidth(80)
        retrieval_layout.addWidget(self.retrieval_mode)


        #retrieve by id
        self.retrieve_id_input = QLineEdit()
        self.retrieve_id_input.setPlaceholderText("Box ID")
        self.retrieve_id_input.setMaximumWidth(50)
        
        retrieval_layout.addWidget(self.retrieve_id_input)

        self.retrieval_mode.currentTextChanged.connect(lambda mode: self.retrieve_id_input.setEnabled(mode == "BY ID"))
        
        self.retrieve_button = QPushButton("Retrieve")
        self.retrieve_button.clicked.connect(self.retrieve_box)
        retrieval_layout.addWidget(self.retrieve_button)
        retrieval_group.setLayout(retrieval_layout)
        operations_layout.addWidget(retrieval_group)
        
        # System
        system_group = QGroupBox("⚙️ System")
        system_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_state)
        system_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_rack)
        system_layout.addWidget(self.reset_button)
        system_group.setLayout(system_layout)
        operations_layout.addWidget(system_group)
        
        operations_layout.addStretch()
        main_layout.addLayout(operations_layout)
        
        # Status
        self.status_label = QLabel("🚛 Trolley at origin (19, 0) - Ready")
        self.status_label.setStyleSheet("padding: 4px; background-color: #f0f0f0; font-size: 11px; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # Grid - SMALLER CELLS
        self.table = QTableWidget(GRID_ROWS, GRID_COLS)
        self.table.setFixedSize(GRID_COLS * 25 + 40, GRID_ROWS * 25 + 40)
        
        for i in range(GRID_ROWS):
            self.table.setRowHeight(i, 25)
        for i in range(GRID_COLS):
            self.table.setColumnWidth(i, 25)
        
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Center table
        table_container = QHBoxLayout()
        table_container.addStretch()
        table_container.addWidget(self.table)
        table_container.addStretch()
        main_layout.addLayout(table_container)
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("padding: 5px; font-size: 11px; background-color: #e3f2fd;")
        main_layout.addWidget(self.stats_label)
        
        # Order
        self.order_label = QLabel()
        self.order_label.setStyleSheet("padding: 4px; font-size: 10px; background-color: #fff3e0;")
        main_layout.addWidget(self.order_label)
        
        # Legend - COMPACT
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))
        
        for text, color in [("Empty", EMPTY_COLOR), ("Occupied", OCCUPIED_COLOR), 
                           ("Trolley", TROLLEY_COLOR), ("Path", PATH_COLOR), 
                           ("Storing", PLACING_COLOR), ("Retrieving", RETRIEVING_COLOR)]:
            label = QLabel(f" {text} ")
            label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black; padding: 2px; font-size: 9px;")
            if text in ["Occupied", "Trolley"]:
                label.setStyleSheet(label.styleSheet() + "color: white;")
            legend_layout.addWidget(label)
        
        legend_layout.addStretch()
        main_layout.addLayout(legend_layout)
    
    def update_grid_display(self):
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                
                if self.trolley_row == row and self.trolley_col == col:
                    item.setBackground(TROLLEY_COLOR)
                    item.setText("🚛")
                    item.setForeground(Qt.white)
                elif (row, col) in self.path_visualization:
                    item.setBackground(PATH_COLOR)
                    item.setText("•")
                elif self.rack.grid[row][col] is None:
                    item.setBackground(EMPTY_COLOR)
                    item.setText("")
                else:
                    box_id = self.rack.grid[row][col]
                    item.setBackground(OCCUPIED_COLOR)
                    item.setText(str(box_id))
                    item.setForeground(Qt.white)
                
                self.table.setItem(row, col, item)
    
    def update_stats(self):
        total_cells = GRID_ROWS * GRID_COLS
        occupied = self.rack.get_occupied_cells()
        empty = total_cells - occupied
        num_boxes = len(self.rack.boxes)
        capacity = (occupied * 100) // total_cells if total_cells > 0 else 0
        
        stats_text = f"📦 Boxes: {num_boxes} | Occupied: {occupied} | Empty: {empty} | Capacity: {capacity}%"
        self.stats_label.setText(stats_text)
        
        if self.rack.box_order:
            order_text = f"📋 Order: {' → '.join(map(str, self.rack.box_order[:20]))}"
            if len(self.rack.box_order) > 20:
                order_text += f"... ({len(self.rack.box_order)} total)"
        else:
            order_text = "📋 Order: (empty)"
        self.order_label.setText(order_text)
    
    def add_box(self):
        if self.is_animating:
            return
        
        try:
            length = int(self.length_input.text())
            width = int(self.width_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Enter valid numbers")
            return
        
        if length <= 0 or width <= 0 or length > GRID_COLS or width > GRID_ROWS:
            QMessageBox.warning(self, "Invalid", f"Dimensions: 1-{GRID_COLS} (L), 1-{GRID_ROWS} (W)")
            return
        
        box = Box(length, width)
        target = self.rack.find_closest_available_location(box, ORIGIN_ROW, ORIGIN_COL)
        
        if target is None:
            QMessageBox.warning(self, "No Space", f"No space for {length}x{width}!")
            return
        
        path = a_star_pathfinding(self.rack.grid, (self.trolley_row, self.trolley_col), target)
        self.start_storage_animation(box, target, path)
    
    def retrieve_box(self):
        if self.is_animating or len(self.rack.boxes) == 0:
            return
        
        mode = self.retrieval_mode.currentText()
        if mode == 'LIFO':
            box_id = self.rack.get_lifo_box()
            mode_name = "LIFO"
        elif mode == 'FIFO':
            box_id = self.rack.get_fifo_box()
            mode_name = "FIFO"
        elif mode == 'BY ID':
            try:
                box_id = int(self.retrieve_id_input.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid", "Enter valid Box ID")
                return
            if box_id not in self.rack.boxes:
                QMessageBox.warning(self, "Not Found", f"Box ID {box_id} not found!")
                return
            mode_name = f"BY ID ({box_id})"
        else:
            return
        target_row, target_col = self.rack.box_positions[box_id]
        path = a_star_pathfinding(self.rack.grid, (self.trolley_row, self.trolley_col), (target_row, target_col))    
        self.start_retrieval_animation(box_id, (target_row, target_col), path, mode_name)

        if box_id is None:
            return
        
        target_row, target_col = self.rack.box_positions[box_id]
        path = a_star_pathfinding(self.rack.grid, (self.trolley_row, self.trolley_col), 
                                  (target_row, target_col))
        
        self.start_retrieval_animation(box_id, (target_row, target_col), path, mode)
    
    def start_storage_animation(self, box, position, path):
        self.is_animating = True
        self.operation_mode = 'storing_moving'
        self.pending_box = box
        self.pending_position = position
        self.trolley_path = path
        self.path_visualization = set(path)
        self.animation_cell_index = 0
        
        self.status_label.setText(f"📦 STORAGE: Moving to ({position[0]},{position[1]}) | Dist: {len(path)}")
        self.add_button.setEnabled(False)
        self.retrieve_button.setEnabled(False)
        self.update_grid_display()
        self.animation_timer.start(150)
    
    def start_retrieval_animation(self, box_id, position, path, mode_name):
        self.is_animating = True
        self.operation_mode = 'retrieving_moving'
        self.retrieving_box_id = box_id
        self.pending_position = position
        self.trolley_path = path
        self.path_visualization = set(path)
        self.animation_cell_index = 0
        
        self.status_label.setText(f"🔄 RETRIEVAL ({mode_name}): Box #{box_id} at ({position[0]},{position[1]})")
        self.add_button.setEnabled(False)
        self.retrieve_button.setEnabled(False)
        self.update_grid_display()
        self.animation_timer.start(150)
    
    def animate(self):
        if self.operation_mode == 'storing_moving':
            if self.trolley_path:
                next_row, next_col = self.trolley_path.pop(0)
                self.trolley_row = next_row
                self.trolley_col = next_col
                self.update_grid_display()
                
                if not self.trolley_path:
                    self.operation_mode = 'storing_placing'
                    self.animation_cell_index = 0
                    
                    self.animation_cells = []
                    start_row, start_col = self.pending_position
                    for r in range(start_row, start_row + self.pending_box.width):
                        for c in range(start_col, start_col + self.pending_box.length):
                            self.animation_cells.append((r, c))
                    
                    self.path_visualization.clear()
                    self.status_label.setText(f"📦 Placing...")
                    self.update_grid_display()
        
        elif self.operation_mode == 'storing_placing':
            if self.animation_cell_index < len(self.animation_cells):
                row, col = self.animation_cells[self.animation_cell_index]
                item = self.table.item(row, col)
                item.setBackground(PLACING_COLOR)
                item.setText("📦")
                self.animation_cell_index += 1
            else:
                self.rack.place_box(self.pending_box, self.pending_position[0], self.pending_position[1])
                self.operation_mode = 'returning'
                self.trolley_path = a_star_pathfinding(self.rack.grid, 
                                                      (self.trolley_row, self.trolley_col),
                                                      (ORIGIN_ROW, ORIGIN_COL))
                self.status_label.setText(f"🔄 Returning...")
                self.update_grid_display()
        
        elif self.operation_mode == 'retrieving_moving':
            if self.trolley_path:
                next_row, next_col = self.trolley_path.pop(0)
                self.trolley_row = next_row
                self.trolley_col = next_col
                self.update_grid_display()
                
                if not self.trolley_path:
                    self.operation_mode = 'retrieving_picking'
                    self.animation_cell_index = 0
                    
                    box = self.rack.boxes[self.retrieving_box_id]
                    start_row, start_col = self.pending_position
                    self.animation_cells = []
                    for r in range(start_row, start_row + box.width):
                        for c in range(start_col, start_col + box.length):
                            self.animation_cells.append((r, c))
                    
                    self.path_visualization.clear()
                    self.status_label.setText(f"🔄 Picking...")
                    self.update_grid_display()
        
        elif self.operation_mode == 'retrieving_picking':
            if self.animation_cell_index < len(self.animation_cells):
                row, col = self.animation_cells[self.animation_cell_index]
                item = self.table.item(row, col)
                item.setBackground(RETRIEVING_COLOR)
                item.setText("⬆️")
                self.animation_cell_index += 1
            else:
                self.rack.remove_box(self.retrieving_box_id)
                self.operation_mode = 'returning'
                self.trolley_path = a_star_pathfinding(self.rack.grid, 
                                                      (self.trolley_row, self.trolley_col),
                                                      (ORIGIN_ROW, ORIGIN_COL))
                self.status_label.setText(f"🔄 Returning with Box #{self.retrieving_box_id}...")
                self.update_grid_display()
        
        elif self.operation_mode == 'returning':
            if self.trolley_path:
                next_row, next_col = self.trolley_path.pop(0)
                self.trolley_row = next_row
                self.trolley_col = next_col
                self.update_grid_display()
                
                if not self.trolley_path:
                    self.animation_timer.stop()
                    self.is_animating = False
                    
                    if hasattr(self, 'pending_box') and self.pending_box:
                        self.status_label.setText(f"✅ Box #{self.pending_box.box_id} stored!")
                        self.length_input.clear()
                        self.width_input.clear()
                    else:
                        self.status_label.setText(f"✅ Box #{self.retrieving_box_id} retrieved!")
                    
                    self.operation_mode = 'idle'
                    self.add_button.setEnabled(True)
                    self.retrieve_button.setEnabled(True)
                    
                    self.update_grid_display()
                    self.update_stats()
                    save_game_state(self.rack)
    
    def save_state(self):
        if save_game_state(self.rack):
            QMessageBox.information(self, "Saved", "State saved!")
    
    def reset_rack(self):
        reply = QMessageBox.question(self, "Reset", "Reset entire rack?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.rack = Rack(GRID_ROWS, GRID_COLS)
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            
            self.trolley_row = ORIGIN_ROW
            self.trolley_col = ORIGIN_COL
            self.path_visualization.clear()
            
            self.update_grid_display()
            self.update_stats()
            self.status_label.setText("🔄 Rack reset")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ASRSWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
