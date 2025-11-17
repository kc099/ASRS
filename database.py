"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - DATABASE FUNCTIONS
============================================================================
"""

import sqlite3
import csv
from config import DATABASE

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
