import matplotlib
matplotlib.use('Qt5Agg')
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtGui import QColor
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import COLORS, GRID_ROWS, GRID_COLS, RACK_HEIGHT_LEVELS, AISLE_COUNT, MODEL_ZONES
from database import get_analytics_data

class Realistic3DViewer(QWidget):
    """Professional Realistic 3D Warehouse Rack System"""
    
    def __init__(self, rack, parent=None):
        super().__init__(parent)
        self.rack = rack
        self.ax = None
        self.rotation_angle = 45
        self.elevation_angle = 20
        
        # Professional dark theme
        self.setStyleSheet(f"""
            QWidget {{
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
            QMessageBox.information(self, "✅ Exported", f"View exported to:\n{filename}")
    
    def get_capacity(self):
        """Calculate capacity"""
        total = GRID_ROWS * GRID_COLS
        occupied = self.rack.get_occupied_cells()
        return int((occupied * 100) / total) if total > 0 else 0