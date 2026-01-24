"""HUD - Heads-Up Display"""

import logging
from direct.gui.DirectGui import DirectFrame, DirectLabel
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TextNode, TransparencyAttrib

logger = logging.getLogger(__name__)


class HUD:
    """Game HUD showing HP, Energy, Level"""
    
    def __init__(self, base):
        """
        Initialize HUD
        
        Args:
            base: ShowBase instance
        """
        self.base = base
        
        # Use aspect2d for HUD elements (screen-space coordinates)
        # This ensures HUD scales properly in fullscreen
        self.hud_root = base.aspect2d.attachNewNode("HUD")
        
        # Create UI elements
        self._create_hp_display()
        self._create_energy_display()
        self._create_level_display()
        self._create_survival_time_display()
        
        logger.info("HUD initialized")
    
    def _create_hp_display(self):
        """Create HP hearts display"""
        # Use normalized aspect2d coordinates (top-left corner: -1, 1)
        self.hp_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(0, 0.25, 0, 0.08),
            pos=(-0.95, 0, 0.9),
            parent=self.hud_root
        )
        
        self.hp_label = DirectLabel(
            text="HP:",
            text_scale=0.06,
            text_fg=(1, 0.2, 0.2, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.04),
            parent=self.hp_frame
        )
        
        self.hp_value_label = DirectLabel(
            text="3/3",
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0.12, 0, 0.04),
            parent=self.hp_frame
        )
        
        # Hearts (using simple ASCII symbols compatible with default font)
        self.hearts_label = DirectLabel(
            text="###",
            text_scale=0.08,
            text_fg=(1, 0.2, 0.2, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0.25, 0, 0.04),
            parent=self.hp_frame
        )
    
    def _create_energy_display(self):
        """Create energy bar"""
        # Use normalized aspect2d coordinates
        self.energy_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(0, 0.25, 0, 0.08),
            pos=(-0.95, 0, 0.75),
            parent=self.hud_root
        )
        
        self.energy_label = DirectLabel(
            text="Energy:",
            text_scale=0.05,
            text_fg=(0.3, 0.8, 1.0, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.02),  # Moved down slightly
            parent=self.energy_frame
        )
        
        # Energy bar background (moved below label text)
        self.energy_bar_bg = DirectFrame(
            frameColor=(0.2, 0.2, 0.2, 0.8),
            frameSize=(0, 0.15, 0, 0.04),
            pos=(0.08, 0, -0.02),  # Moved down below text
            parent=self.energy_frame
        )
        
        # Energy bar foreground
        self.energy_bar = DirectFrame(
            frameColor=(0.3, 0.8, 1.0, 1.0),
            frameSize=(0, 0.15, 0, 0.04),
            pos=(0.08, 0, -0.02),  # Moved down below text
            parent=self.energy_frame
        )
        
        # Energy percentage text (moved next to bar)
        self.energy_text = DirectLabel(
            text="100%",
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0.18, 0, -0.02),  # Aligned with bar
            parent=self.energy_frame
        )
    
    def _create_level_display(self):
        """Create level display"""
        # Use normalized aspect2d coordinates
        self.level_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(0, 0.15, 0, 0.08),
            pos=(-0.95, 0, 0.6),
            parent=self.hud_root
        )
        
        self.level_label = DirectLabel(
            text="Level: 1",
            text_scale=0.05,
            text_fg=(1, 1, 0, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.04),
            parent=self.level_frame
        )
    
    def _create_survival_time_display(self):
        """Create survival time display (for minigame)"""
        self.survival_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(0, 0.2, 0, 0.08),
            pos=(-0.95, 0, 0.45),
            parent=self.hud_root
        )
        
        self.survival_label = DirectLabel(
            text="Time: 0.0s",
            text_scale=0.05,
            text_fg=(0, 1, 0, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.04),
            parent=self.survival_frame
        )
        
        # Hide by default (only show in minigame)
        self.survival_frame.hide()
    
    def update_hp(self, current: int, maximum: int):
        """Update HP display"""
        self.hp_value_label['text'] = f"{current}/{maximum}"
        
        # Update hearts (using simple ASCII symbols compatible with default font)
        hearts = "#" * current + "_" * (maximum - current)
        self.hearts_label['text'] = hearts
        
        # Color based on HP
        if current <= 1:
            color = (1, 0, 0, 1)  # Red
        elif current <= maximum // 2:
            color = (1, 0.5, 0, 1)  # Orange
        else:
            color = (1, 0.2, 0.2, 1)  # Normal red
        
        self.hearts_label['text_fg'] = color
    
    def update_energy(self, percentage: float):
        """
        Update energy bar
        
        Args:
            percentage: 0.0 to 1.0
        """
        # Clamp percentage
        percentage = max(0.0, min(1.0, percentage))
        
        # Update bar width (keep position and height, only change width)
        self.energy_bar['frameSize'] = (0, 0.15 * percentage, 0, 0.04)
        
        # Update text
        self.energy_text['text'] = f"{int(percentage * 100)}%"
        
        # Color based on energy level
        if percentage < 0.2:
            color = (1, 0, 0, 1)  # Red
        elif percentage < 0.5:
            color = (1, 0.5, 0, 1)  # Orange
        else:
            color = (0.3, 0.8, 1.0, 1)  # Blue
        
        self.energy_bar['frameColor'] = color
    
    def update_level(self, level: int):
        """Update level display"""
        self.level_label['text'] = f"Level: {level}"
    
    def update_survival_time(self, seconds: float):
        """Update survival time display"""
        self.survival_label['text'] = f"Time: {seconds:.1f}s"
    
    def show_survival_time(self):
        """Show survival time display"""
        self.survival_frame.show()
    
    def hide_survival_time(self):
        """Hide survival time display"""
        self.survival_frame.hide()
    
    def show(self):
        """Show HUD"""
        self.hp_frame.show()
        self.energy_frame.show()
        self.level_frame.show()
    
    def hide(self):
        """Hide HUD"""
        self.hp_frame.hide()
        self.energy_frame.hide()
        self.level_frame.hide()
    
    def cleanup(self):
        """Cleanup HUD"""
        self.hp_frame.destroy()
        self.energy_frame.destroy()
        self.level_frame.destroy()
        self.survival_frame.destroy()