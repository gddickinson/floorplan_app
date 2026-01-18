"""
Export functionality for floor plans.

Provides export to PNG, PDF, and other formats with measurements,
annotations, and professional layouts.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PyQt6.QtCore import QRectF, QSizeF, Qt, QMarginsF
from PyQt6.QtGui import QPainter, QImage, QPdfWriter, QPageSize, QColor, QPen, QFont
from PyQt6.QtWidgets import QFileDialog

logger = logging.getLogger(__name__)


class FloorPlanExporter:
    """
    Export floor plans to various formats.
    
    Supports PNG, PDF with options for including measurements,
    annotations, grid, and title blocks.
    """
    
    def __init__(self, canvas):
        """
        Initialize exporter.
        
        Args:
            canvas: FloorPlanCanvas to export
        """
        self.canvas = canvas
        logger.info("FloorPlanExporter initialized")
    
    def export_to_png(self, filepath: str, width: int = 2400, height: int = 1800,
                      include_grid: bool = True, include_dimensions: bool = True,
                      background_color: str = "#FFFFFF", dpi: int = 300) -> bool:
        """
        Export floor plan to PNG image.
        
        Args:
            filepath: Output file path
            width: Image width in pixels
            height: Image height in pixels
            include_grid: Whether to show grid
            include_dimensions: Whether to show measurements
            background_color: Background color
            dpi: Resolution in dots per inch
            
        Returns:
            True if successful
        """
        try:
            # Create image
            image = QImage(width, height, QImage.Format.Format_RGB32)
            image.fill(QColor(background_color))
            
            # Set DPI for proper scaling
            dpi_ratio = dpi / 96  # 96 is default screen DPI
            image.setDotsPerMeterX(int(dpi * 39.3701))  # Convert DPI to dots/meter
            image.setDotsPerMeterY(int(dpi * 39.3701))
            
            # Create painter
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Save canvas state
            old_grid = self.canvas.show_grid
            self.canvas.show_grid = include_grid
            
            # Calculate scale to fit content
            bounds = self.canvas.floor_plan.get_bounds()
            if bounds:
                min_pt, max_pt = bounds
                content_width = max_pt.x - min_pt.x
                content_height = max_pt.y - min_pt.y
                
                # Add margins (10%)
                margin = 0.1
                content_width *= (1 + 2 * margin)
                content_height *= (1 + 2 * margin)
                
                # Calculate scale to fit
                scale_x = width / content_width if content_width > 0 else 1
                scale_y = height / content_height if content_height > 0 else 1
                scale = min(scale_x, scale_y)
                
                # Center content
                offset_x = (width - content_width * scale) / 2 - min_pt.x * scale
                offset_y = (height - content_height * scale) / 2 - min_pt.y * scale
                
                painter.translate(offset_x, offset_y)
                painter.scale(scale, scale)
            
            # Render canvas content
            self._render_floor_plan(painter, include_dimensions)
            
            # Restore state
            self.canvas.show_grid = old_grid
            
            painter.end()
            
            # Save image
            image.save(filepath, "PNG")
            
            logger.info(f"Exported PNG: {filepath} ({width}×{height} @ {dpi} DPI)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export PNG: {e}")
            return False
    
    def export_to_pdf(self, filepath: str, page_size: str = "Letter",
                     include_grid: bool = True, include_dimensions: bool = True,
                     include_title_block: bool = True, title: str = "",
                     scale: Optional[str] = None) -> bool:
        """
        Export floor plan to PDF.
        
        Args:
            filepath: Output file path
            page_size: Page size ("Letter", "A4", "Tabloid", "A3", etc.)
            include_grid: Whether to show grid
            include_dimensions: Whether to show measurements
            include_title_block: Whether to add title block
            title: Plan title for title block
            scale: Scale notation (e.g., "1/4\" = 1'")
            
        Returns:
            True if successful
        """
        try:
            # Create PDF writer
            pdf = QPdfWriter(filepath)
            
            # Set page size
            if page_size == "Letter":
                pdf.setPageSize(QPageSize.PageSizeId.Letter)
            elif page_size == "A4":
                pdf.setPageSize(QPageSize.PageSizeId.A4)
            elif page_size == "Tabloid":
                pdf.setPageSize(QPageSize.PageSizeId.Tabloid)
            elif page_size == "A3":
                pdf.setPageSize(QPageSize.PageSizeId.A3)
            else:
                pdf.setPageSize(QPageSize.PageSizeId.Letter)
            
            pdf.setResolution(300)  # 300 DPI
            pdf.setPageOrientation(QPageSize.Orientation.Landscape)
            
            # Create painter
            painter = QPainter(pdf)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get page dimensions
            page_rect = painter.viewport()
            
            # Calculate drawing area (leave room for title block)
            if include_title_block:
                title_block_height = page_rect.height() * 0.15
                drawing_rect = QRectF(
                    page_rect.x(),
                    page_rect.y(),
                    page_rect.width(),
                    page_rect.height() - title_block_height
                )
            else:
                drawing_rect = page_rect
            
            # Save canvas state
            old_grid = self.canvas.show_grid
            self.canvas.show_grid = include_grid
            
            # Calculate scale to fit
            bounds = self.canvas.floor_plan.get_bounds()
            if bounds:
                min_pt, max_pt = bounds
                content_width = max_pt.x - min_pt.x
                content_height = max_pt.y - min_pt.y
                
                # Add margins
                margin = 0.05
                content_width *= (1 + 2 * margin)
                content_height *= (1 + 2 * margin)
                
                # Calculate scale
                scale_x = drawing_rect.width() / content_width if content_width > 0 else 1
                scale_y = drawing_rect.height() / content_height if content_height > 0 else 1
                fit_scale = min(scale_x, scale_y)
                
                # Center content
                offset_x = (drawing_rect.width() - content_width * fit_scale) / 2 - min_pt.x * fit_scale
                offset_y = (drawing_rect.height() - content_height * fit_scale) / 2 - min_pt.y * fit_scale
                
                painter.translate(offset_x, offset_y)
                painter.scale(fit_scale, fit_scale)
            
            # Render floor plan
            self._render_floor_plan(painter, include_dimensions)
            
            # Reset transform for title block
            painter.resetTransform()
            
            # Draw title block
            if include_title_block:
                self._draw_title_block(
                    painter, page_rect, title, scale,
                    self.canvas.floor_plan.name
                )
            
            # Restore state
            self.canvas.show_grid = old_grid
            
            painter.end()
            
            logger.info(f"Exported PDF: {filepath} ({page_size})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            return False
    
    def _render_floor_plan(self, painter: QPainter, include_dimensions: bool = True):
        """Render the floor plan content."""
        # Use canvas rendering methods
        if self.canvas.show_grid:
            self.canvas._draw_grid(painter)
        
        self.canvas._draw_rooms(painter)
        self.canvas._draw_walls(painter)
        self.canvas._draw_openings(painter)
        self.canvas._draw_furniture_items(painter)
        self.canvas._draw_fixtures(painter)
        self.canvas._draw_stairs(painter)
        
        if include_dimensions:
            self.canvas._draw_measurements(painter)
    
    def _draw_title_block(self, painter: QPainter, page_rect: QRectF,
                         title: str, scale: Optional[str], project_name: str):
        """Draw professional title block at bottom of page."""
        # Title block area
        tb_height = page_rect.height() * 0.15
        tb_rect = QRectF(
            page_rect.x(),
            page_rect.height() - tb_height,
            page_rect.width(),
            tb_height
        )
        
        # Draw border
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawRect(tb_rect)
        
        # Draw dividing lines
        painter.drawLine(
            int(tb_rect.x() + tb_rect.width() * 0.6),
            int(tb_rect.y()),
            int(tb_rect.x() + tb_rect.width() * 0.6),
            int(tb_rect.bottom())
        )
        
        # Project title (left side)
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#000000"))
        
        title_text = title or project_name or "Floor Plan"
        painter.drawText(
            QRectF(tb_rect.x() + 20, tb_rect.y() + 10,
                  tb_rect.width() * 0.55, tb_rect.height() / 2),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title_text
        )
        
        # Info fields (right side)
        info_font = QFont("Arial", 12)
        painter.setFont(info_font)
        
        info_x = tb_rect.x() + tb_rect.width() * 0.62
        info_y = tb_rect.y() + 20
        line_height = 30
        
        # Date
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        painter.drawText(int(info_x), int(info_y), f"Date: {date_str}")
        
        # Scale
        if scale:
            info_y += line_height
            painter.drawText(int(info_x), int(info_y), f"Scale: {scale}")
        else:
            info_y += line_height
            painter.drawText(int(info_x), int(info_y), "Scale: As shown")
        
        # Drawn by
        info_y += line_height
        painter.drawText(int(info_x), int(info_y), "Drawn by: Floor Plan Editor v1.2")
    
    @staticmethod
    def get_export_dialog_png(parent=None) -> Optional[str]:
        """Show file dialog for PNG export."""
        filepath, _ = QFileDialog.getSaveFileName(
            parent,
            "Export as PNG",
            "",
            "PNG Images (*.png);;All Files (*)"
        )
        return filepath if filepath else None
    
    @staticmethod
    def get_export_dialog_pdf(parent=None) -> Optional[str]:
        """Show file dialog for PDF export."""
        filepath, _ = QFileDialog.getSaveFileName(
            parent,
            "Export as PDF",
            "",
            "PDF Documents (*.pdf);;All Files (*)"
        )
        return filepath if filepath else None
