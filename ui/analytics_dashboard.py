"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - ANALYTICS DASHBOARD
============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTabWidget, QWidget, QGridLayout, QTableWidget, QTableWidgetItem,
    QFileDialog
)
from PySide6.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from config import COLORS, DATABASE, GRID_ROWS, GRID_COLS
from database import get_analytics_data, export_to_csv

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
