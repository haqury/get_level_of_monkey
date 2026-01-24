"""
Input Manager - управление вводом от клавиатуры и BrainLink
"""

import logging
from typing import Optional, Callable
from direct.showbase.DirectObject import DirectObject
from src.integration import BrainLinkClient

logger = logging.getLogger(__name__)


class InputManager(DirectObject):
    """
    Менеджер ввода - обрабатывает клавиатуру и BrainLink
    
    Supports:
    - Keyboard input (arrows, space)
    - BrainLink input via Shared Memory
    """
    
    def __init__(self, base, brainlink_enabled: bool = True):
        """
        Initialize input manager
        
        Args:
            base: Panda3D ShowBase instance
            brainlink_enabled: Enable BrainLink integration
        """
        super().__init__()
        
        self.base = base
        self.brainlink_enabled = brainlink_enabled
        
        # BrainLink client
        self.brainlink: Optional[BrainLinkClient] = None
        if brainlink_enabled:
            from src.integration import get_brainlink_client
            # Try default name first
            memory_name = "brainlink_data"
            # If launcher found a different name, use it
            if hasattr(base, 'brainlink_launcher') and hasattr(base.brainlink_launcher, '_found_memory_name'):
                if base.brainlink_launcher._found_memory_name:
                    memory_name = base.brainlink_launcher._found_memory_name
                    logger.info(f"Using found memory name: {memory_name}")
            
            self.brainlink = get_brainlink_client(memory_name)
            if not self.brainlink.connect():
                logger.warning("BrainLink not available, using keyboard only")
                self.brainlink_enabled = False
        
        # Current input state
        self.move_direction = (0, 0)  # (x, y)
        self.action_pressed = False
        
        # Callbacks
        self.on_action: Optional[Callable] = None
        
        # Keyboard state
        self.keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "space": False,
        }
        
        # Setup keyboard bindings
        self._setup_keyboard()
        
        # Last BrainLink event
        self.last_bl_event = ""
        
        logger.info(f"InputManager initialized (BrainLink: {brainlink_enabled})")
    
    def _setup_keyboard(self):
        """Setup keyboard event handlers"""
        # Movement keys
        self.accept("arrow_up", self._on_key, ["up", True])
        self.accept("arrow_up-up", self._on_key, ["up", False])
        
        self.accept("arrow_down", self._on_key, ["down", True])
        self.accept("arrow_down-up", self._on_key, ["down", False])
        
        self.accept("arrow_left", self._on_key, ["left", True])
        self.accept("arrow_left-up", self._on_key, ["left", False])
        
        self.accept("arrow_right", self._on_key, ["right", True])
        self.accept("arrow_right-up", self._on_key, ["right", False])
        
        # Action key
        self.accept("space", self._on_key, ["space", True])
        self.accept("space-up", self._on_key, ["space", False])
        
        logger.debug("Keyboard bindings set up")
    
    def _on_key(self, key: str, pressed: bool):
        """Handle keyboard event"""
        self.keys[key] = pressed
        
        # Trigger action callback
        if key == "space" and pressed and self.on_action:
            self.on_action()
    
    def update(self, dt: float):
        """
        Update input state (called every frame)
        
        Args:
            dt: Delta time
        """
        # Get BrainLink input (if enabled)
        bl_event = ""
        if self.brainlink_enabled and self.brainlink:
            bl_event = self.brainlink.get_event()
        
        # Calculate movement direction
        x, y = 0, 0
        
        # BrainLink has priority over keyboard
        if bl_event:
            if bl_event == "ml":  # Move Left
                x = -1
            elif bl_event == "mr":  # Move Right
                x = 1
            elif bl_event == "mu":  # Move Up
                y = 1
            elif bl_event == "md":  # Move Down
                y = -1
            elif bl_event == "stop":
                x, y = 0, 0
            
            # Log event changes
            if bl_event != self.last_bl_event:
                logger.debug(f"🧠 BrainLink event: {bl_event}")
                self.last_bl_event = bl_event
        
        # Fallback to keyboard if no BrainLink event
        else:
            if self.keys["left"]:
                x -= 1
            if self.keys["right"]:
                x += 1
            if self.keys["up"]:
                y += 1
            if self.keys["down"]:
                y -= 1
        
        # Normalize diagonal movement
        if x != 0 and y != 0:
            length = (x * x + y * y) ** 0.5
            x /= length
            y /= length
        
        self.move_direction = (x, y)
        self.action_pressed = self.keys["space"]
    
    def get_movement(self) -> tuple:
        """
        Get current movement direction
        
        Returns:
            (x, y) normalized direction vector
        """
        return self.move_direction
    
    def is_action_pressed(self) -> bool:
        """Check if action key is pressed"""
        return self.action_pressed
    
    def cleanup(self):
        """Cleanup resources"""
        self.ignoreAll()
        
        if self.brainlink:
            self.brainlink.disconnect()
        
        logger.info("InputManager cleaned up")
