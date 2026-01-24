"""Main Menu scene"""

import logging
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


class MainMenuScene(BaseScene):
    """Главное меню игры"""
    
    def __init__(self, base):
        super().__init__(base, "MainMenu")
        
        # Callbacks
        self.on_play = None
        self.on_quit = None
        
        # Create UI
        self._create_ui()
        
        logger.info("MainMenu scene created")
    
    def _create_ui(self):
        """Create menu UI"""
        # Get font with Cyrillic support if available
        font = None
        if hasattr(self.base, 'cyrillic_font') and self.base.cyrillic_font:
            font = self.base.cyrillic_font
        
        # Title
        self.title = OnscreenText(
            text="Fucking Pickup",
            pos=(0, 0.7),
            scale=0.15,
            fg=(1, 1, 0, 1),
            shadow=(0, 0, 0, 0.8),
            mayChange=False,
            font=font
        )
        
        # Subtitle
        self.subtitle = OnscreenText(
            text="2D Action with BrainLink Integration",
            pos=(0, 0.55),
            scale=0.05,
            fg=(0.8, 0.8, 0.8, 1),
            mayChange=False,
            font=font
        )
        
        # BrainLink status frame
        self.status_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.8),
            frameSize=(-0.7, 0.7, -0.2, 0.2),
            pos=(0, 0, 0.05)
        )
        
        # BrainLink status label
        self.brainlink_status_label = DirectLabel(
            text="BrainLink Status:",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.08),
            parent=self.status_frame,
            text_font=font
        )
        
        # Status text
        self.status_text = DirectLabel(
            text="Checking...",
            text_scale=0.05,
            text_fg=(1, 1, 0, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.0),
            parent=self.status_frame,
            text_font=font
        )
        
        # Info text
        self.info_text = DirectLabel(
            text="Searching for BrainLinkClient...",
            text_scale=0.04,
            text_fg=(0.7, 0.7, 0.7, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.08),
            parent=self.status_frame,
            text_font=font
        )
        
        # Play button
        self.play_btn = DirectButton(
            text="Play",
            text_scale=0.07,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.6, 0.2, 1),
            frameSize=(-0.5, 0.5, -0.2, 0.2),
            pos=(0, 0, -0.2),
            command=self._on_play_clicked,
            text_font=font
        )
        self.play_btn['state'] = 'disabled'  # Disabled until BrainLink ready
        # Apply font to all text components
        if font:
            self._apply_font_to_button(self.play_btn, font)

        # Settings button
        self.settings_btn = DirectButton(
            text="Config",
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.6, 1),
            frameSize=(-0.4, 0.4, -0.18, 0.18),
            pos=(0, 0, -0.45),
            command=self._on_settings_clicked,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.settings_btn, font)
        
        # Quit button
        self.quit_btn = DirectButton(
            text="Quit",
            text_scale=0.07,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.2, 0.2, 1),
            frameSize=(-0.5, 0.5, -0.2, 0.2),
            pos=(0, 0, -0.7),
            command=self._on_quit_clicked,
            text_font=font
        )
        # Apply font to all text components
        if font:
            self._apply_font_to_button(self.quit_btn, font)
        
        # Controls info
        self.controls_text = OnscreenText(
            text="Controls: Arrow Keys or BrainLink (ml/mr/mu/md)",
            pos=(0, -0.8),
            scale=0.04,
            fg=(0.6, 0.6, 0.6, 1),
            mayChange=False,
            font=font
        )

        # Settings panel (hidden by default)
        self._create_settings_panel(font)
        
        # Hide all initially
        self._hide_all()
    
    def _hide_all(self):
        """Hide all UI elements"""
        self.title.hide()
        self.subtitle.hide()
        self.status_frame.hide()
        self.play_btn.hide()
        self.settings_btn.hide()
        self.quit_btn.hide()
        self.controls_text.hide()
        if hasattr(self, 'settings_frame'):
            self.settings_frame.hide()
    
    def _show_all(self):
        """Show all UI elements"""
        self.title.show()
        self.subtitle.show()
        self.status_frame.show()
        self.play_btn.show()
        self.settings_btn.show()
        self.quit_btn.show()
        self.controls_text.show()
        # Settings frame stays hidden unless opened
    
    def enter(self, player=None):
        """Enter menu"""
        super().enter(player)
        self._show_all()
        logger.info("Main menu displayed")
    
    def exit(self):
        """Exit menu"""
        super().exit()
        self._hide_all()
    
    def update_brainlink_status(self, status: str, info: str = "", color: tuple = (1, 1, 0, 1)):
        """
        Update BrainLink status display
        
        Args:
            status: Status text
            info: Additional info
            color: Status text color
        """
        self.status_text['text'] = status
        self.status_text['text_fg'] = color
        self.info_text['text'] = info
    
    def enable_play_button(self):
        """Enable play button"""
        self.play_btn['state'] = 'normal'
        self.play_btn['frameColor'] = (0.2, 0.8, 0.2, 1)
    
    def disable_play_button(self):
        """Disable play button"""
        self.play_btn['state'] = 'disabled'
        self.play_btn['frameColor'] = (0.3, 0.3, 0.3, 1)
    
    def _on_play_clicked(self):
        """Handle play button click"""
        logger.info("Play button clicked")
        if self.on_play:
            self.on_play()
    
    def _on_quit_clicked(self):
        """Handle quit button click"""
        logger.info("Quit button clicked")
        if self.on_quit:
            self.on_quit()

    # === Settings / Config ===
    def _create_settings_panel(self, font):
        """Create settings (config) panel for resolution selection"""
        # Semi-transparent background frame
        self.settings_frame = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-0.7, 0.7, -0.5, 0.5),
            pos=(0, 0, 0.0)
        )

        # Title
        self.settings_title = DirectLabel(
            text="Settings",
            text_scale=0.07,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.35),
            parent=self.settings_frame,
            text_font=font
        )

        # Resolution options
        def add_resolution_button(text, width, height, fullscreen, z):
            btn = DirectButton(
                text=text,
                text_scale=0.05,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.3, 0.3, 0.3, 1),
                frameSize=(-0.6, 0.6, -0.12, 0.12),
                pos=(0, 0, z),
                command=self._apply_resolution,
                extraArgs=[width, height, fullscreen],
                parent=self.settings_frame,
                text_font=font
            )
            if font:
                self._apply_font_to_button(btn, font)
            return btn

        # Common resolutions
        self.btn_res_1280 = add_resolution_button(
            "1280 x 720 (Windowed)", 1280, 720, False, 0.15
        )
        self.btn_res_1600 = add_resolution_button(
            "1600 x 900 (Windowed)", 1600, 900, False, 0.0
        )
        self.btn_res_1920 = add_resolution_button(
            "1920 x 1080 (Fullscreen)", 1920, 1080, True, -0.15
        )

        # Close button
        self.settings_close_btn = DirectButton(
            text="Close",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.4, 0.2, 0.2, 1),
            frameSize=(-0.4, 0.4, -0.12, 0.12),
            pos=(0, 0, -0.35),
            command=self._on_settings_clicked,  # toggle
            parent=self.settings_frame,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.settings_close_btn, font)

        self.settings_frame.hide()

    def _on_settings_clicked(self):
        """Toggle settings panel visibility"""
        if self.settings_frame.isHidden():
            self.settings_frame.show()
        else:
            self.settings_frame.hide()

    def _apply_resolution(self, width: int, height: int, fullscreen: bool):
        """Apply resolution via Game.apply_resolution"""
        logger.info(f"Settings: applying resolution {width}x{height}, fullscreen={fullscreen}")
        try:
            if hasattr(self.base, "apply_resolution"):
                self.base.apply_resolution(width, height, fullscreen)
            else:
                logger.warning("Base has no 'apply_resolution' method")
        except Exception as e:
            logger.error(f"Failed to apply resolution from settings: {e}")
    
    def _apply_font_to_button(self, button, font):
        """Apply font to all text components of a button"""
        try:
            button['text_font'] = font
            # Try to get text component and set font directly
            for i in range(4):  # DirectButton has text0, text1, text2, text3
                text_comp = button.component(f'text{i}')
                if text_comp:
                    text_comp.setFont(font)
        except Exception as e:
            logger.debug(f"Could not apply font to button: {e}")
    
    def cleanup(self):
        """Cleanup"""
        super().cleanup()
        
        self.title.destroy()
        self.subtitle.destroy()
        self.status_frame.destroy()
        self.play_btn.destroy()
        self.quit_btn.destroy()
        self.controls_text.destroy()
