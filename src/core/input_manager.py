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
        logger.info(f"🎮 InputManager: brainlink_enabled={brainlink_enabled}")
        if brainlink_enabled:
            from src.integration import get_brainlink_client
            # Try default name first
            memory_name = "brainlink_data"
            # If launcher found a different name, use it
            if hasattr(base, 'brainlink_launcher') and hasattr(base.brainlink_launcher, '_found_memory_name'):
                if base.brainlink_launcher._found_memory_name:
                    memory_name = base.brainlink_launcher._found_memory_name
                    logger.info(f"Using found memory name: {memory_name}")
            
            logger.info(f"🎮 InputManager: Getting BrainLink client (memory_name: {memory_name})")
            self.brainlink = get_brainlink_client(memory_name)
            logger.info(f"🎮 InputManager: BrainLink client created: {self.brainlink is not None}")
            logger.info(f"🎮 InputManager: Attempting to connect to BrainLink (memory_name: {memory_name})")
            if not self.brainlink.connect():
                logger.warning("🎮 InputManager: BrainLink not available, using keyboard only")
                self.brainlink_enabled = False
            else:
                logger.info("🎮 InputManager: BrainLink connected successfully!")
        else:
            logger.info("🎮 InputManager: BrainLink disabled in config")
        
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
        
        # Track if BrainLink is being used
        self._is_using_brainlink = False
        
        # Event tracking for sending to BrainLink
        self.last_keyboard_event = ""
        self.last_brainlink_event_sent = ""
        self.send_keyboard_events = False
        self.send_brainlink_events = False
        self.send_to_history = False
        self.send_to_ml = False
        
        # Get config from base if available
        if hasattr(base, 'game_config'):
            bl_config = base.game_config.get("brainlink", {})
            self.send_keyboard_events = bl_config.get("send_keyboard_events", False)
            self.send_brainlink_events = bl_config.get("send_brainlink_events", True)  # Default: enabled
            self.send_to_history = bl_config.get("send_to_history", False)
            self.send_to_ml = bl_config.get("send_to_ml", False)
        
        logger.info(f"🎮 InputManager initialized (BrainLink: {brainlink_enabled}, send_keyboard: {self.send_keyboard_events}, brainlink_obj: {self.brainlink is not None})")
    
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
        
        # Escape — pause menu (forward to game)
        self.accept("escape", self._on_escape_key)
        
        logger.debug("Keyboard bindings set up")
    
    def _on_escape_key(self):
        """Escape key — open pause menu if in game."""
        if hasattr(self.base, "_on_escape"):
            self.base._on_escape()
    
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
        self._current_ml_event = ""  # For HUD when BrainLink off
        # Get BrainLink input (if enabled)
        bl_event = ""
        if self.brainlink_enabled and self.brainlink:
            if not self.brainlink.is_connected():
                # Try to reconnect
                if not hasattr(self, '_reconnect_logged'):
                    logger.warning("🎮 InputManager: BrainLink disconnected, attempting reconnect...")
                    self._reconnect_logged = True
                self.brainlink.connect()
            else:
                if hasattr(self, '_reconnect_logged'):
                    self._reconnect_logged = False
                bl_event = self.brainlink.get_event()
                self._current_ml_event = bl_event  # For HUD
                # Log every event read (for debugging)
                if bl_event and bl_event != self.last_bl_event:
                    logger.info(f"🎮 InputManager: BrainLink event read: '{bl_event}'")
                # Also log if we're reading but getting empty events (periodically)
                if not hasattr(self, '_empty_event_counter'):
                    self._empty_event_counter = 0
                if not bl_event or bl_event == "":
                    self._empty_event_counter += 1
                    if self._empty_event_counter % 300 == 0:  # Log every 5 seconds at 60fps
                        logger.debug(f"🎮 InputManager: Reading from BrainLink but getting empty events (counter: {self._empty_event_counter})")
                else:
                    self._empty_event_counter = 0
        else:
            # BrainLink not enabled or not available
            if not hasattr(self, '_brainlink_disabled_logged'):
                logger.info(f"🎮 InputManager: BrainLink disabled or not available (enabled={self.brainlink_enabled}, brainlink={self.brainlink is not None})")
                self._brainlink_disabled_logged = True
        
        # Calculate movement direction
        x, y = 0, 0
        
        # Keyboard has priority over BrainLink
        keyboard_event = ""
        if self.keys["left"]:
            x -= 1
            keyboard_event = "ml"
        elif self.keys["right"]:
            x += 1
            keyboard_event = "mr"
        elif self.keys["up"]:
            y += 1
            keyboard_event = "mu"
        elif self.keys["down"]:
            y -= 1
            keyboard_event = "md"
        
        # If keyboard is not used, fallback to BrainLink
        if not keyboard_event and bl_event:
            if bl_event == "ml":  # Move Left
                x = -1
                logger.info(f"🎮 InputManager: Applying BrainLink movement LEFT (x={x}, y={y})")
            elif bl_event == "mr":  # Move Right
                x = 1
                logger.info(f"🎮 InputManager: Applying BrainLink movement RIGHT (x={x}, y={y})")
            elif bl_event == "mu":  # Move Up
                y = 1
                logger.info(f"🎮 InputManager: Applying BrainLink movement UP (x={x}, y={y})")
            elif bl_event == "md":  # Move Down
                y = -1
                logger.info(f"🎮 InputManager: Applying BrainLink movement DOWN (x={x}, y={y})")
            elif bl_event == "stop":
                x, y = 0, 0
                logger.info(f"🎮 InputManager: Applying BrainLink STOP (x={x}, y={y})")
            
            # Log event changes
            if bl_event != self.last_bl_event:
                logger.info(f"🧠 InputManager: BrainLink event changed: '{self.last_bl_event}' -> '{bl_event}'")
                self.last_bl_event = bl_event
                
                # Send BrainLink events to ML training if enabled
                if self.send_brainlink_events and bl_event and bl_event != "stop":
                    if bl_event != self.last_brainlink_event_sent and self.brainlink:
                        if self.send_to_ml:
                            self.brainlink.send_event_for_ml_training(bl_event)
                            logger.debug(f"📤 Sent BrainLink event '{bl_event}' for ML training")
                        if self.send_to_history:
                            self.brainlink.send_event_to_history(bl_event)
                        self.last_brainlink_event_sent = bl_event
        
        # Send keyboard events to BrainLink if enabled (always, even if BrainLink is active)
        if self.send_keyboard_events and keyboard_event and keyboard_event != self.last_keyboard_event:
            if self.brainlink:
                if self.send_to_history:
                    self.brainlink.send_event_to_history(keyboard_event)
                if self.send_to_ml:
                    self.brainlink.send_event_for_ml_training(keyboard_event)
            self.last_keyboard_event = keyboard_event
        
        # Normalize diagonal movement
        if x != 0 and y != 0:
            length = (x * x + y * y) ** 0.5
            x /= length
            y /= length
        
        self.move_direction = (x, y)
        self.action_pressed = self.keys["space"]
        
        # Track if BrainLink is being used for movement (only if keyboard is not used)
        self._is_using_brainlink = bool(not keyboard_event and bl_event and bl_event != "stop")
        
        # Periodic logging for debugging (every 60 frames ~ 1 second at 60fps)
        if not hasattr(self, '_debug_counter'):
            self._debug_counter = 0
        self._debug_counter += 1
        if self._debug_counter % 60 == 0 and self._is_using_brainlink:
            logger.info(f"🎮 InputManager: BrainLink active - event='{bl_event}', movement=({x:.2f}, {y:.2f}), keyboard_event='{keyboard_event}'")
    
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
    
    def is_using_brainlink(self) -> bool:
        """
        Check if movement is controlled by BrainLink
        
        Returns:
            True if BrainLink is providing movement input, False if keyboard
        """
        return getattr(self, '_is_using_brainlink', False)

    def get_ml_display_info(self) -> tuple:
        """
        Get current ML model stats for HUD.
        
        Returns:
            (prediction, connected, confidence, probs): prediction string, connection,
            confidence 0.0-1.0, and dict of class probabilities (ml, mr, mu, md, stop)
        """
        pred = getattr(self, '_current_ml_event', "") or "—"
        connected = self.brainlink.is_connected() if self.brainlink else False
        confidence, probs = (0.0, {}) if not self.brainlink else self.brainlink.get_ml_stats()
        return (pred, connected, confidence, probs)
    
    def cleanup(self):
        """Cleanup resources"""
        self.ignoreAll()
        
        if self.brainlink:
            self.brainlink.disconnect()
        
        logger.info("InputManager cleaned up")
