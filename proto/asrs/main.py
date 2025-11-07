"""
============================================================================
ASRS WAREHOUSE MANAGEMENT SYSTEM - MAIN ENTRY POINT
============================================================================
"""

import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import BusinessASRSMainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("ASRS Warehouse Management System")
    app.setOrganizationName("Professional Warehouse Solutions")
    app.setApplicationVersion("2.0")
    
    # Create and show main window
    window = BusinessASRSMainWindow()

    # Show maximized for large screens, normal for others
    if window.should_maximize:
        window.showMaximized()
    else:
        window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
