"""
Undo/Redo system for floor plan editing.

Provides command pattern implementation for reversible operations.
"""

import logging
from typing import List, Any, Dict
from dataclasses import dataclass, field
from copy import deepcopy

from core import FloorPlan


logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Base class for undoable commands."""
    
    def execute(self, floor_plan: FloorPlan) -> None:
        """Execute the command."""
        raise NotImplementedError
    
    def undo(self, floor_plan: FloorPlan) -> None:
        """Undo the command."""
        raise NotImplementedError
    
    def description(self) -> str:
        """Get command description for display."""
        return self.__class__.__name__


@dataclass
class AddWallCommand(Command):
    """Command to add a wall."""
    wall: Any
    wall_id: str = ""
    
    def execute(self, floor_plan: FloorPlan) -> None:
        self.wall_id = floor_plan.add_wall(self.wall)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        floor_plan.remove_wall(self.wall_id)
    
    def description(self) -> str:
        return f"Add Wall ({self.wall.length():.1f}\")"


@dataclass
class RemoveWallCommand(Command):
    """Command to remove a wall."""
    wall_id: str
    wall: Any = None
    removed_openings: List[Any] = field(default_factory=list)
    
    def execute(self, floor_plan: FloorPlan) -> None:
        # Store wall data before removal
        self.wall = floor_plan.get_wall(self.wall_id)
        # Store openings that will be removed
        self.removed_openings = [
            o for o in floor_plan.openings if o.wall_id == self.wall_id
        ]
        floor_plan.remove_wall(self.wall_id)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        # Restore the wall
        floor_plan.walls.append(self.wall)
        # Restore openings
        for opening in self.removed_openings:
            floor_plan.openings.append(opening)
    
    def description(self) -> str:
        return "Remove Wall"


@dataclass
class AddOpeningCommand(Command):
    """Command to add an opening."""
    opening: Any
    opening_id: str = ""
    
    def execute(self, floor_plan: FloorPlan) -> None:
        self.opening_id = floor_plan.add_opening(self.opening)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        floor_plan.remove_opening(self.opening_id)
    
    def description(self) -> str:
        return f"Add {self.opening.opening_type.value.title()}"


@dataclass
class RemoveOpeningCommand(Command):
    """Command to remove an opening."""
    opening_id: str
    opening: Any = None
    
    def execute(self, floor_plan: FloorPlan) -> None:
        # Find and store the opening
        for opening in floor_plan.openings:
            if opening.id == self.opening_id:
                self.opening = opening
                break
        floor_plan.remove_opening(self.opening_id)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        floor_plan.openings.append(self.opening)
    
    def description(self) -> str:
        return "Remove Opening"


@dataclass
class AddRoomCommand(Command):
    """Command to add a room."""
    room: Any
    room_id: str = ""
    
    def execute(self, floor_plan: FloorPlan) -> None:
        self.room_id = floor_plan.add_room(self.room)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        floor_plan.remove_room(self.room_id)
    
    def description(self) -> str:
        return f"Add Room: {self.room.name}"


@dataclass
class RemoveRoomCommand(Command):
    """Command to remove a room."""
    room_id: str
    room: Any = None
    
    def execute(self, floor_plan: FloorPlan) -> None:
        for room in floor_plan.rooms:
            if room.id == self.room_id:
                self.room = room
                break
        floor_plan.remove_room(self.room_id)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        floor_plan.rooms.append(self.room)
    
    def description(self) -> str:
        return "Remove Room"


@dataclass
class ModifyPropertyCommand(Command):
    """Command to modify a property of an object."""
    object_id: str
    object_type: str  # 'wall', 'opening', 'room'
    property_name: str
    old_value: Any
    new_value: Any
    
    def execute(self, floor_plan: FloorPlan) -> None:
        obj = self._get_object(floor_plan)
        if obj:
            setattr(obj, self.property_name, self.new_value)
    
    def undo(self, floor_plan: FloorPlan) -> None:
        obj = self._get_object(floor_plan)
        if obj:
            setattr(obj, self.property_name, self.old_value)
    
    def _get_object(self, floor_plan: FloorPlan):
        """Get the object being modified."""
        if self.object_type == 'wall':
            return floor_plan.get_wall(self.object_id)
        elif self.object_type == 'opening':
            for opening in floor_plan.openings:
                if opening.id == self.object_id:
                    return opening
        elif self.object_type == 'room':
            for room in floor_plan.rooms:
                if room.id == self.object_id:
                    return room
        return None
    
    def description(self) -> str:
        return f"Modify {self.object_type.title()} {self.property_name}"


class UndoStack:
    """
    Manages undo/redo operations using the command pattern.
    
    Provides standard undo/redo functionality with a command history.
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.commands: List[Command] = []
        self.current_index = -1
        
        logger.info(f"UndoStack initialized (max_size={max_size})")
    
    def execute_command(self, command: Command, floor_plan: FloorPlan) -> None:
        """
        Execute a command and add it to the stack.
        
        Args:
            command: Command to execute
            floor_plan: Floor plan to operate on
        """
        # Execute the command
        command.execute(floor_plan)
        
        # Remove any commands after current index (we're branching)
        self.commands = self.commands[:self.current_index + 1]
        
        # Add new command
        self.commands.append(command)
        self.current_index += 1
        
        # Limit stack size
        if len(self.commands) > self.max_size:
            self.commands.pop(0)
            self.current_index -= 1
        
        logger.debug(f"Executed: {command.description()} (stack size: {len(self.commands)})")
    
    def undo(self, floor_plan: FloorPlan) -> bool:
        """
        Undo the last command.
        
        Args:
            floor_plan: Floor plan to operate on
            
        Returns:
            True if undo was successful, False otherwise
        """
        if not self.can_undo():
            logger.warning("Cannot undo: no commands in history")
            return False
        
        command = self.commands[self.current_index]
        command.undo(floor_plan)
        self.current_index -= 1
        
        logger.info(f"Undid: {command.description()}")
        return True
    
    def redo(self, floor_plan: FloorPlan) -> bool:
        """
        Redo the next command.
        
        Args:
            floor_plan: Floor plan to operate on
            
        Returns:
            True if redo was successful, False otherwise
        """
        if not self.can_redo():
            logger.warning("Cannot redo: no commands to redo")
            return False
        
        self.current_index += 1
        command = self.commands[self.current_index]
        command.execute(floor_plan)
        
        logger.info(f"Redid: {command.description()}")
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.current_index < len(self.commands) - 1
    
    def get_undo_text(self) -> str:
        """Get text for undo action."""
        if self.can_undo():
            return f"Undo {self.commands[self.current_index].description()}"
        return "Undo"
    
    def get_redo_text(self) -> str:
        """Get text for redo action."""
        if self.can_redo():
            return f"Redo {self.commands[self.current_index + 1].description()}"
        return "Redo"
    
    def clear(self):
        """Clear all commands from the stack."""
        self.commands.clear()
        self.current_index = -1
        logger.info("UndoStack cleared")
    
    def get_history(self) -> List[str]:
        """Get list of command descriptions in history."""
        return [cmd.description() for cmd in self.commands]

