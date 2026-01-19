"""
Utilities module for floor plan application.
"""

from .logging_config import (
    setup_logging,
    get_default_log_file,
    AppConfig,
    format_dimension,
    inches_to_feet,
    feet_to_inches
)
from .undo_stack import (
    UndoStack,
    Command,
    AddWallCommand,
    RemoveWallCommand,
    AddOpeningCommand,
    RemoveOpeningCommand,
    AddRoomCommand,
    RemoveRoomCommand,
    ModifyPropertyCommand
)
from .measurements import (
    MeasurementTool,
    calculate_room_area,
    calculate_perimeter,
    get_floor_plan_statistics,
    format_statistics
)
from .clipboard import (
    Clipboard,
    get_clipboard
)
from .transforms import (
    MoveTransform,
    RotateTransform,
    ArrayTool
)
from .annotations import (
    TextAnnotation,
    DimensionLine,
    AnnotationManager
)
from .export import (
    FloorPlanExporter
)
from .iphone_importer import (
    iPhoneScanImporter,
    import_iphone_scan
)
from .roomplan_importer import (
    RoomPlanImporter,
    import_roomplan_json,
    import_roomplan_to_building
)

__all__ = [
    'setup_logging',
    'get_default_log_file',
    'AppConfig',
    'format_dimension',
    'inches_to_feet',
    'feet_to_inches',
    'UndoStack',
    'Command',
    'AddWallCommand',
    'RemoveWallCommand',
    'AddOpeningCommand',
    'RemoveOpeningCommand',
    'AddRoomCommand',
    'RemoveRoomCommand',
    'ModifyPropertyCommand',
    'MeasurementTool',
    'calculate_room_area',
    'calculate_perimeter',
    'get_floor_plan_statistics',
    'format_statistics',
    'Clipboard',
    'get_clipboard',
    'MoveTransform',
    'RotateTransform',
    'ArrayTool',
    'TextAnnotation',
    'DimensionLine',
    'AnnotationManager',
    'FloorPlanExporter',
    'iPhoneScanImporter',
    'import_iphone_scan',
    'RoomPlanImporter',
    'import_roomplan_json',
    'import_roomplan_to_building'
]
