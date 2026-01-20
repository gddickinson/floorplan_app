"""
Utility functions and logging configuration for the floor plan application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console_output: Whether to also log to console
    
    Returns:
        Configured root logger
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized at {log_level} level")
    if log_file:
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def get_default_log_file() -> str:
    """Get default log file path in user's home directory."""
    log_dir = Path.home() / ".floorplan_app" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(log_dir / f"floorplan_{timestamp}.log")


class AppConfig:
    """Application configuration settings."""
    
    # Default drawing settings
    DEFAULT_WALL_THICKNESS = 6.0  # inches
    DEFAULT_DOOR_WIDTH = 36.0  # inches
    DEFAULT_WINDOW_WIDTH = 48.0  # inches
    
    # Canvas settings
    GRID_SIZE = 12.0  # inches (1 foot grid)
    SNAP_TOLERANCE = 6.0  # inches (snap to grid if within this distance)
    
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


def format_dimension(inches: float, unit: str = "ft") -> str:
    """
    Format a dimension in inches to a readable string.
    
    Args:
        inches: Dimension in inches
        unit: Target unit ('ft', 'in', or 'auto')
    
    Returns:
        Formatted string (e.g., "10' 6\"" or "126\"")
    """
    if unit == "in":
        return f'{inches:.1f}"'
    elif unit == "ft" or (unit == "auto" and inches >= 12):
        feet = int(inches // 12)
        remaining_inches = inches % 12
        if remaining_inches < 0.1:
            return f"{feet}'"
        else:
            return f"{feet}' {remaining_inches:.1f}\""
    else:
        return f'{inches:.1f}"'


def inches_to_feet(inches: float) -> float:
    """Convert inches to feet."""
    return inches / 12.0


def feet_to_inches(feet: float) -> float:
    """Convert feet to inches."""
    return feet * 12.0

