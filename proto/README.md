# ASRS Warehouse Management System

This project is a professional, business-grade Automated Storage and Retrieval System (ASRS) with a realistic 3D visualization.

## How to Run the Application

To run the application, navigate to the project's root directory (`/home/pc/Lohith/ABB/proto/`) in your terminal and execute the following command:

```bash
python -m asrs.main
```

This will launch the main application window.

## Project Structure

The code has been refactored into a modular structure for better maintainability:

- `asrs/`: Main application package.
  - `main.py`: The main entry point of the application.
  - `config.py`: Contains all application constants and configurations.
  - `database.py`: Handles all SQLite database interactions.
  - `core.py`: Contains the core logic classes (`Box`, `Rack`).
  - `pathfinding.py`: Includes the A* pathfinding algorithm.
  - `ui/`: Contains all User Interface components.
    - `main_window.py`: The main application window.
    - `analytics_dashboard.py`: The analytics dashboard dialog.
    - `realistic_3d_viewer.py`: The realistic 3D viewer dialog.
- `intial/asrs_complete/`: Contains an archived version of the original, non-refactored script.
