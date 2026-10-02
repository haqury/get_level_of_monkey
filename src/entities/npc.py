"""NPC entities"""

import logging
from pathlib import Path
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CardMaker, Vec3
from src.core.i18n import t, resolve_dialog

logger = logging.getLogger(__name__)


class NPC(DirectObject):
    """Base NPC class"""
    
    def __init__(self, base, name: str, pos: tuple, color: tuple = (1, 1, 0)):
        """
        Initialize NPC
        
        Args:
            base: ShowBase instance
            name: NPC name
            pos: Position (x, y)
            color: RGB color tuple
        """
        super().__init__()
        
        self.base = base
        self.name = name
        self.position = Vec3(pos[0], 0, pos[1])
        self.color = color
        
        # Dialogs
        self.dialogs = []
        self.current_dialog_index = 0
        
        # Visual
        self.sprite_path = None  # Will be set by subclasses
        self.node = self._create_visual()
        self.node.reparentTo(base.render)
        self.node.setPos(self.position)
        
        # Interaction
        self.can_interact = True
        self.interaction_range = 10.0  # 2.0 * 5 (for 5x larger locations)
        
        logger.info(f"NPC '{name}' created at {pos}")
    
    def _create_visual(self):
        """Create NPC visual with sprite"""
        cm = CardMaker(f"npc_{self.name}")
        cm.setFrame(-0.6, 0.6, -0.6, 0.6)
        
        node = self.base.render.attachNewNode(cm.generate())
        
        # Load sprite texture if available
        if self.sprite_path:
            sprite_file = Path("assets/sprites/npc") / self.sprite_path
            if sprite_file.exists():
                try:
                    texture = self.base.loader.loadTexture(str(sprite_file))
                    node.setTexture(texture)
                    node.setTwoSided(True)
                    logger.debug(f"Loaded sprite for {self.name}: {sprite_file}")
                except Exception as e:
                    logger.warning(f"Could not load sprite for {self.name}: {e}")
                    node.setColor(*self.color, 1.0)
            else:
                node.setColor(*self.color, 1.0)
        else:
            # Fallback: use color
            node.setColor(*self.color, 1.0)
        
        node.setBillboardPointEye()
        
        return node
    
    def add_dialog(self, text_key: str, options: list = None):
        """Add dialog by i18n key."""
        self.dialogs.append({"text_key": text_key, "options": options})
    
    def get_current_dialog(self):
        """Get current dialog with translated text."""
        if 0 <= self.current_dialog_index < len(self.dialogs):
            entry = self.dialogs[self.current_dialog_index]
            return resolve_dialog({"text_key": entry["text_key"], "options": entry.get("options")})
        return None
    
    def refresh_locale(self):
        """Update display name after language change."""
        if getattr(self, "_name_key", None):
            self.name = t(self._name_key)
    
    def next_dialog(self):
        """Move to next dialog"""
        self.current_dialog_index = min(
            self.current_dialog_index + 1,
            len(self.dialogs) - 1
        )
    
    def reset_dialog(self):
        """Reset to first dialog"""
        self.current_dialog_index = 0
    
    def is_in_range(self, player_pos: tuple) -> bool:
        """Check if player is in interaction range"""
        dx = player_pos[0] - self.position.x
        dy = player_pos[1] - self.position.z
        distance = (dx*dx + dy*dy) ** 0.5
        return distance <= self.interaction_range
    
    def cleanup(self):
        """Cleanup"""
        if self.node:
            self.node.removeNode()
        self.ignoreAll()


class Father(NPC):
    """Отец NPC"""
    
    def __init__(self, base, pos: tuple):
        super().__init__(base, "Father", pos, color=(0.8, 0.4, 0.2))
        self._name_key = "npc.father.name"
        self.name = t(self._name_key)
        
        # Set sprite path
        self.sprite_path = "father.png"
        
        # Reload visual with sprite
        if self.node:
            self.node.removeNode()
        self.node = self._create_visual()
        self.node.reparentTo(base.render)
        self.node.setPos(self.position)
        
        # Setup dialogs
        # Dialog when talking to father directly
        self.add_dialog("npc.father.dialog1")
        self.add_dialog("npc.father.dialog2")
        
        self.exit_dialog = {
            "text_key": "npc.father.exit",
            "option_keys": [
                ("npc.father.play_minigame", lambda: None),
            ],
        }


class Mother(NPC):
    """Мама NPC"""
    
    def __init__(self, base, pos: tuple):
        super().__init__(base, "Mother", pos, color=(1.0, 0.6, 0.8))
        self._name_key = "npc.mother.name"
        self.name = t(self._name_key)
        
        # Set sprite path
        self.sprite_path = "mother.png"
        self.cooking_frame = 0  # For cooking animation
        self.cooking_timer = 0.0
        
        # Reload visual with sprite
        if self.node:
            self.node.removeNode()
        self.node = self._create_visual()
        self.node.reparentTo(base.render)
        self.node.setPos(self.position)
        
        # Setup dialogs
        self.add_dialog("npc.mother.dialog1")
        self.add_dialog("npc.mother.dialog2")
    
    def update_cooking_animation(self, dt: float):
        """Update cooking animation"""
        self.cooking_timer += dt
        if self.cooking_timer >= 0.5:  # Switch frame every 0.5 seconds
            self.cooking_timer = 0.0
            self.cooking_frame = 1 - self.cooking_frame  # Toggle 0/1
            
            # Reload sprite for new frame
            if self.cooking_frame == 1:
                self.sprite_path = "mother_cook1.png"
            else:
                self.sprite_path = "mother.png"
            
            # Update visual
            if self.node:
                old_node = self.node
                self.node = self._create_visual()
                self.node.reparentTo(self.base.render)
                self.node.setPos(self.position)
                old_node.removeNode()