"""
Application configuration constants (no GUI dependencies; re-exported by utils.logging_config).
"""

from pathlib import Path

from .snapping import GRID_SIZE, SNAP_TOLERANCE


class AppConfig:
    """Application configuration settings."""
    
    # Default drawing settings
    DEFAULT_WALL_THICKNESS = 6.0  # inches
    DEFAULT_DOOR_WIDTH = 36.0  # inches
    DEFAULT_WINDOW_WIDTH = 48.0  # inches
    
    # Canvas settings
    GRID_SIZE = GRID_SIZE  # inches (1 foot grid)
    SNAP_TOLERANCE = SNAP_TOLERANCE  # inches (snap to wall endpoints within this distance)
    
    # Visual settings
    CANVAS_BG_COLOR = "#FFFFFF"
    GRID_COLOR = "#E0E0E0"
    WALL_COLOR = "#000000"
    SELECTED_COLOR = "#FF0000"
    DOOR_COLOR = "#8B4513"
    WINDOW_COLOR = "#87CEEB"
    
    # Scale settings (pixels per inch at 100% zoom)
    DEFAULT_SCALE = 2.0  # 2 pixels per inch
    MIN_SCALE = 0.5
    MAX_SCALE = 10.0
    
    # File settings
    FILE_EXTENSION = ".floorplan"
    FILE_FILTER = "Floor Plan Files (*.floorplan);;All Files (*)"
    
    # Recent files
    MAX_RECENT_FILES = 10
    
    @classmethod
    def get_config_dir(cls) -> Path:
        """Get application configuration directory."""
        config_dir = Path.home() / ".floorplan_app"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @classmethod
    def get_recent_files_path(cls) -> Path:
        """Get path to recent files list."""
        return cls.get_config_dir() / "recent_files.txt"
