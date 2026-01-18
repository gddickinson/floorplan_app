#!/usr/bin/env python3
"""
Floor Plan Editor - Main Application Entry Point

A modular, extensible application for creating 2D architectural floor plans.

Usage:
    python main.py [file.floorplan]

Features:
    - Interactive wall drawing with grid snapping
    - Door and window placement
    - Save/load floor plans (JSON format)
    - Zoom, pan, and fit-to-view
    - Comprehensive logging
    - Modular, expandable architecture

Author: Created for architectural planning and visualization
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from utils import setup_logging, get_default_log_file, AppConfig
from gui import MainWindow
from core import FloorPlan

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Setup logging
    log_file = get_default_log_file()
    setup_logging(log_level="INFO", log_file=log_file, console_output=True)
    
    logger.info("=" * 60)
    logger.info("Floor Plan Editor Starting")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_file}")
    
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Floor Plan Editor")
    app.setOrganizationName("FloorPlan")
    
    # Create main window
    window = MainWindow()
    
    # Check if a file was provided as command-line argument
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if file_path.exists() and file_path.suffix == AppConfig.FILE_EXTENSION:
            try:
                floor_plan = FloorPlan.load_from_file(str(file_path))
                window.canvas.set_floor_plan(floor_plan)
                window.current_file = file_path
                window.update_title()
                logger.info(f"Loaded floor plan from command line: {file_path}")
            except Exception as e:
                logger.error(f"Failed to load file from command line: {e}")
    
    # Show window
    window.show()
    
    logger.info("Application window displayed")
    
    # Run application
    exit_code = app.exec()
    
    logger.info(f"Application exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
