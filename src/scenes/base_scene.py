"""Base scene class"""

import logging
from direct.showbase.DirectObject import DirectObject

logger = logging.getLogger(__name__)


class BaseScene(DirectObject):
    """Base class for all game scenes/locations"""
    
    def __init__(self, base, name: str):
        """
        Initialize scene
        
        Args:
            base: ShowBase instance
            name: Scene name
        """
        super().__init__()
        
        self.base = base
        self.name = name
        self.is_active = False
        
        # Entities
        self.npcs = []
        self.exits = []  # List of dicts: {"name": str, "pos": tuple, "target_scene": str}
        
        logger.info(f"Scene '{name}' created")
    
    def enter(self, player):
        """
        Called when entering this scene
        
        Args:
            player: Player object
        """
        self.is_active = True
        logger.info(f"Entered scene: {self.name}")
    
    def exit(self):
        """Called when exiting this scene"""
        self.is_active = False
        logger.info(f"Exited scene: {self.name}")
    
    def update(self, dt: float):
        """Update scene (called every frame)"""
        pass
    
    def check_exits(self, player_pos: tuple):
        """
        Check if player is near an exit
        
        Args:
            player_pos: (x, y)
        
        Returns:
            Exit dict or None
        """
        for exit_info in self.exits:
            exit_pos = exit_info["pos"]
            dx = player_pos[0] - exit_pos[0]
            dy = player_pos[1] - exit_pos[1]
            distance = (dx*dx + dy*dy) ** 0.5
            
            if distance < 3.0:  # Interaction range - adjusted for smaller room size
                return exit_info
        
        return None
    
    def get_nearby_npc(self, player_pos: tuple):
        """Get NPC in interaction range"""
        for npc in self.npcs:
            if npc.is_in_range(player_pos):
                return npc
        return None
    
    def cleanup(self):
        """Cleanup scene"""
        for npc in self.npcs:
            npc.cleanup()
        self.npcs.clear()
        self.ignoreAll()
