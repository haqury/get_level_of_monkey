"""Main Menu scene"""

import logging
import json
from pathlib import Path
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DirectEntry
from tkinter import filedialog
import tkinter as tk
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, CardMaker
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


class MainMenuScene(BaseScene):
    """Главное меню игры"""
    
    def __init__(self, base):
        super().__init__(base, "MainMenu")
        
        # Callbacks
        self.on_play = None
        self.on_quit = None
        
        # Background elements
        self.background = None
        
        # Create UI
        self._create_background()
        self._create_ui()
        
        logger.info("MainMenu scene created")
    
    def _create_background(self):
        """Create modern gradient background for menu"""
        # Create a large background card covering the screen
        cm = CardMaker("menu_bg")
        cm.setFrame(-2, 2, -1.5, 1.5)  # Full screen coverage
        
        self.background = self.base.render2d.attachNewNode(cm.generate())
        self.background.setPos(0, 0, 0)
        # Dark blue-purple gradient effect (using solid color as approximation)
        self.background.setColor(0.08, 0.05, 0.15, 1.0)  # Dark purple-blue
        self.background.setTransparency(0)
        
        # Create a subtle overlay for depth
        cm_overlay = CardMaker("menu_overlay")
        cm_overlay.setFrame(-2, 2, -1.5, 1.5)
        overlay = self.base.render2d.attachNewNode(cm_overlay.generate())
        overlay.setPos(0, 0, -0.01)  # Slightly behind main background
        overlay.setColor(0.05, 0.03, 0.1, 0.3)  # Subtle overlay
        overlay.setTransparency(1)
        self.background_overlay = overlay
        
        logger.debug("Menu background created")
    
    def _create_ui(self):
        """Create menu UI"""
        # Get font with Cyrillic support if available
        font = None
        if hasattr(self.base, 'cyrillic_font') and self.base.cyrillic_font:
            font = self.base.cyrillic_font
        
        # Title - properly scaled for modern resolutions
        self.title = OnscreenText(
            text="Get Level of Monkey",
            pos=(0, 0.65),
            scale=0.12,
            fg=(1.0, 0.9, 0.3, 1),  # Golden yellow
            shadow=(0, 0, 0, 1.0),
            shadowOffset=(0.02, 0.02),
            mayChange=False,
            font=font,
            align=TextNode.ACenter
        )
        
        # Subtitle - properly scaled
        self.subtitle = OnscreenText(
            text="2D Action Game with BrainLink Integration",
            pos=(0, 0.52),
            scale=0.035,
            fg=(0.9, 0.9, 0.9, 1),
            shadow=(0, 0, 0, 0.6),
            mayChange=False,
            font=font,
            align=TextNode.ACenter
        )
        
        # BrainLink status frame - compact and modern
        self.status_frame = DirectFrame(
            frameColor=(0.05, 0.05, 0.1, 0.85),
            frameSize=(-0.5, 0.5, -0.08, 0.08),
            pos=(0, 0, 0.35),
            borderWidth=(0.005, 0.005),
            borderUvWidth=(0.005, 0.005)
        )
        
        # BrainLink status label
        self.brainlink_status_label = DirectLabel(
            text="BrainLink Status:",
            text_scale=0.04,
            text_fg=(0.9, 0.9, 1.0, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.03),
            parent=self.status_frame,
            text_font=font
        )
        
        # Status text - properly scaled
        self.status_text = DirectLabel(
            text="Checking...",
            text_scale=0.045,
            text_fg=(1, 1, 0.5, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.02),
            parent=self.status_frame,
            text_font=font
        )
        
        # Info text
        self.info_text = DirectLabel(
            text="Searching for BrainLinkClient...",
            text_scale=0.032,
            text_fg=(0.75, 0.75, 0.75, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.05),
            parent=self.status_frame,
            text_font=font
        )
        
        # Play button - old style, same size as others, moved down, half size
        # Button height is 0.2 (from -0.1 to 0.1), so buttons will be spaced 0.2 apart
        # Moved down by 1/10 screen (0.2 units)
        self.play_btn = DirectButton(
            text="Play",
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.6, 0.2, 1),
            frameSize=(-0.25, 0.25, -0.1, 0.1),
            pos=(0, 0, -0.3),
            command=self._on_play_clicked,
            text_font=font
        )
        self.play_btn['state'] = 'disabled'  # Disabled until BrainLink ready
        # Apply font to all text components
        if font:
            self._apply_font_to_button(self.play_btn, font)

        # Settings button - touching Play button (Play bottom at -0.4, Config top at -0.4, center at -0.5)
        self.settings_btn = DirectButton(
            text="Config",
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.6, 1),
            frameSize=(-0.25, 0.25, -0.1, 0.1),
            pos=(0, 0, -0.5),
            command=self._on_settings_clicked,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.settings_btn, font)
        
        # Quit button - touching Config button (Config bottom at -0.6, Quit top at -0.6, center at -0.7)
        self.quit_btn = DirectButton(
            text="Quit",
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.2, 0.2, 1),
            frameSize=(-0.25, 0.25, -0.1, 0.1),
            pos=(0, 0, -0.7),
            command=self._on_quit_clicked,
            text_font=font
        )
        # Apply font to all text components
        if font:
            self._apply_font_to_button(self.quit_btn, font)
        
        # Controls info - properly scaled, positioned just below Quit button
        self.controls_text = OnscreenText(
            text="Controls: Arrow Keys or BrainLink (ml/mr/mu/md)",
            pos=(0, -0.85),
            scale=0.028,
            fg=(0.7, 0.7, 0.7, 1),
            shadow=(0, 0, 0, 0.5),
            mayChange=False,
            font=font,
            align=TextNode.ACenter
        )

        # Settings panel (hidden by default)
        self._create_settings_panel(font)
        
        # Hide all initially
        self._hide_all()
    
    def _hide_all(self):
        """Hide all UI elements"""
        if self.background:
            self.background.hide()
        if hasattr(self, 'background_overlay') and self.background_overlay:
            self.background_overlay.hide()
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
        if self.background:
            self.background.show()
        if hasattr(self, 'background_overlay') and self.background_overlay:
            self.background_overlay.show()
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
        """Create full settings panel with tabs for different categories"""
        # Semi-transparent background frame - larger for tabs
        self.settings_frame = DirectFrame(
            frameColor=(0.05, 0.05, 0.1, 0.9),
            frameSize=(-0.6, 0.6, -0.5, 0.5),
            pos=(0, 0, 0.0),
            borderWidth=(0.008, 0.008),
            borderUvWidth=(0.008, 0.008)
        )

        # Title
        self.settings_title = DirectLabel(
            text="Settings",
            text_scale=0.055,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.45),
            parent=self.settings_frame,
            text_font=font,
            text_align=TextNode.ACenter
        )

        # Tab buttons
        self._create_settings_tabs(font)
        
        # Content frames for each tab
        self._create_resolution_tab(font)
        self._create_controls_tab(font)
        self._create_brainlink_tab(font)
        
        # Close button
        self.settings_close_btn = DirectButton(
            text="Close",
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.5, 0.2, 0.2, 1),
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            pos=(0, 0, -0.45),
            command=self._on_settings_clicked,
            parent=self.settings_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.005, 0.005)
        )
        if font:
            self._apply_font_to_button(self.settings_close_btn, font)

        # Start with resolution tab active
        self._switch_settings_tab("resolution")
        self.settings_frame.hide()
    
    def _create_settings_tabs(self, font):
        """Create tab buttons for settings categories"""
        self.settings_tabs = {}
        self.current_tab = "resolution"
        
        # Tab button width is 0.36 (from -0.18 to 0.18), so spacing them with gaps
        tab_positions = [
            ("Resolution", "resolution", -0.45),
            ("Controls", "controls", -0.05),
            ("BrainLink", "brainlink", 0.35)
        ]
        
        for text, tab_id, x_pos in tab_positions:
            btn = DirectButton(
                text=text,
                text_scale=0.032,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.2, 0.2, 0.3, 1),
                frameSize=(-0.18, 0.18, -0.05, 0.05),
                pos=(x_pos, 0, 0.35),
                command=self._switch_settings_tab,
                extraArgs=[tab_id],
                parent=self.settings_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.003, 0.003)
            )
            if font:
                self._apply_font_to_button(btn, font)
            self.settings_tabs[tab_id] = btn
    
    def _create_resolution_tab(self, font):
        """Create resolution settings tab"""
        self.resolution_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.55, 0.55, -0.4, 0.25),
            pos=(0, 0, 0.05),
            parent=self.settings_frame
        )
        
        # Resolution label
        DirectLabel(
            text="Resolution:",
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, 0.15),
            parent=self.resolution_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        
        # Resolution buttons
        def add_resolution_button(text, width, height, fullscreen, z):
            btn = DirectButton(
                text=text,
                text_scale=0.032,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.25, 0.25, 0.35, 1),
                frameSize=(-0.45, 0.45, -0.05, 0.05),
                pos=(0, 0, z),
                command=self._apply_resolution,
                extraArgs=[width, height, fullscreen],
                parent=self.resolution_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.005, 0.005)
            )
            if font:
                self._apply_font_to_button(btn, font)
            return btn

        self.btn_res_1280 = add_resolution_button("1280 x 720 (Windowed)", 1280, 720, False, 0.05)
        self.btn_res_1600 = add_resolution_button("1600 x 900 (Windowed)", 1600, 900, False, -0.05)
        self.btn_res_1920 = add_resolution_button("1920 x 1080 (Fullscreen)", 1920, 1080, True, -0.15)
    
    def _create_controls_tab(self, font):
        """Create controls settings tab with cheater mode"""
        self.controls_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.55, 0.55, -0.4, 0.25),
            pos=(0, 0, 0.05),
            parent=self.settings_frame
        )
        
        # Get current cheater mode setting
        cheater_mode = False
        if hasattr(self.base, 'game_config'):
            cheater_mode = self.base.game_config.get("player", {}).get("cheater_mode", False)
        
        # Cheater Mode checkbox
        DirectLabel(
            text="Cheater Mode:",
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.4, 0, 0.1),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        
        DirectLabel(
            text="(Unlimited Energy)",
            text_scale=0.03,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.4, 0, 0.0),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        
        # Cheater mode checkbox button
        self.cheater_mode_checkbox = DirectButton(
            text="✓" if cheater_mode else " ",
            text_scale=0.04,
            text_fg=(0, 1, 0, 1) if cheater_mode else (0.5, 0.5, 0.5, 1),
            frameColor=(0.2, 0.2, 0.3, 1),
            frameSize=(-0.05, 0.05, -0.04, 0.04),
            pos=(0.35, 0, 0.05),
            command=self._toggle_cheater_mode,
            parent=self.controls_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )
        
        # Controls configuration placeholder
        DirectLabel(
            text="Controls configuration",
            text_scale=0.035,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.1),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ACenter
        )
        
        DirectLabel(
            text="(Coming soon)",
            text_scale=0.028,
            text_fg=(0.5, 0.5, 0.5, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.15),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ACenter
        )
    
    def _create_brainlink_tab(self, font):
        """Create BrainLink settings tab"""
        self.brainlink_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.55, 0.55, -0.48, 0.25),
            pos=(0, 0, 0.05),
            parent=self.settings_frame
        )
        
        # Get current BrainLink config
        bl_config = {}
        if hasattr(self.base, 'game_config'):
            bl_config = self.base.game_config.get("brainlink", {})
        
        # BrainLink settings checkboxes (same style as other tabs: button as checkbox)
        settings = [
            ("Send Keyboard Events", "send_keyboard_events", 0.15, bl_config.get("send_keyboard_events", True)),
            ("Send to History", "send_to_history", 0.05, bl_config.get("send_to_history", True)),
            ("Send to ML Training", "send_to_ml", -0.05, bl_config.get("send_to_ml", True)),
            ("Send BrainLink Events", "send_brainlink_events", -0.15, bl_config.get("send_brainlink_events", True)),
            ("Stop pauses game", "stop_pauses_game", -0.20, bl_config.get("stop_pauses_game", False)),
        ]
        
        self.brainlink_checkboxes = {}
        for label, key, z_pos, default_value in settings:
            # Label
            DirectLabel(
                text=label + ":",
                text_scale=0.035,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(-0.4, 0, z_pos),
                parent=self.brainlink_frame,
                text_font=font,
                text_align=TextNode.ALeft
            )
            
            # Checkbox (using button as checkbox)
            checkbox = DirectButton(
                text="✓" if default_value else " ",
                text_scale=0.04,
                text_fg=(0, 1, 0, 1) if default_value else (0.5, 0.5, 0.5, 1),
                frameColor=(0.2, 0.2, 0.3, 1),
                frameSize=(-0.05, 0.05, -0.04, 0.04),
                pos=(0.35, 0, z_pos),
                command=self._toggle_brainlink_setting,
                extraArgs=[key],
                parent=self.brainlink_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.003, 0.003)
            )
            self.brainlink_checkboxes[key] = checkbox
        
        # ML config: confidence threshold
        DirectLabel(
            text="Confidence threshold:",
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.4, 0, -0.28),
            parent=self.brainlink_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        thresh_val = bl_config.get("confidence_threshold", 0.5)
        self.brainlink_threshold_entry = DirectEntry(
            scale=0.032,
            initialText=str(thresh_val),
            numLines=1,
            width=8,
            pos=(0.1, 0, -0.28),
            parent=self.brainlink_frame,
            text_font=font,
            focusInCommand=self._brainlink_entry_focus_in,
            focusOutCommand=self._brainlink_apply_ml_config,
            frameColor=(0.2, 0.2, 0.3, 1),
            frameSize=(0, 0.25, -0.02, 0.02)
        )
        
        # ML config: prediction weights (ml, mr, mu, md)
        DirectLabel(
            text="Weights (ml,mr,mu,md):",
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.4, 0, -0.36),
            parent=self.brainlink_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        weights = bl_config.get("prediction_weights", [1.0, 1.0, 1.0, 1.0])
        weights_str = ", ".join(str(round(w, 2)) for w in (weights + [1.0] * 4)[:4])
        self.brainlink_weights_entry = DirectEntry(
            scale=0.03,
            initialText=weights_str,
            numLines=1,
            width=18,
            pos=(0.05, 0, -0.36),
            parent=self.brainlink_frame,
            text_font=font,
            focusInCommand=self._brainlink_entry_focus_in,
            focusOutCommand=self._brainlink_apply_ml_config,
            frameColor=(0.2, 0.2, 0.3, 1),
            frameSize=(0, 0.4, -0.02, 0.02)
        )
        
        # Apply button for ML config
        DirectButton(
            text="Apply",
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.08, 0.08, -0.04, 0.04),
            pos=(0.48, 0, -0.32),
            command=self._brainlink_apply_ml_config,
            parent=self.brainlink_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )
        
        # Load / Save model buttons
        DirectButton(
            text="Load model",
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.25, 0.4, 1),
            frameSize=(-0.12, 0.12, -0.04, 0.04),
            pos=(-0.2, 0, -0.44),
            command=self._brainlink_load_model,
            parent=self.brainlink_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )
        DirectButton(
            text="Save model",
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.12, 0.12, -0.04, 0.04),
            pos=(0.2, 0, -0.44),
            command=self._brainlink_save_model,
            parent=self.brainlink_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )
    
    def _brainlink_entry_focus_in(self, *args, **kwargs):
        """Optional: clear placeholder on focus (no-op for now)."""
        pass
    
    def _brainlink_apply_ml_config(self, *args, **kwargs):
        """Read threshold and weights from entries and save to config."""
        if not hasattr(self.base, 'game_config'):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        try:
            thresh_text = self.brainlink_threshold_entry.get()
            thresh = float(thresh_text.strip())
            thresh = max(0.0, min(1.0, thresh))
            bl_config["confidence_threshold"] = thresh
        except (ValueError, TypeError):
            pass
        try:
            weights_text = self.brainlink_weights_entry.get()
            parts = [p.strip() for p in weights_text.split(",")]
            weights = [float(x) for x in parts[:4]]
            if len(weights) < 4:
                weights.extend([1.0] * (4 - len(weights)))
            bl_config["prediction_weights"] = weights[:4]
        except (ValueError, TypeError):
            pass
        self.base.game_config["brainlink"] = bl_config
        self._save_brainlink_config()
        logger.info("BrainLink ML config (threshold, weights) applied and saved")
    
    def _brainlink_load_model(self):
        """Open file dialog to choose model file; save path to config."""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Load ML model",
            filetypes=[("Model files", "*.pkl *.joblib *.pt *.onnx"), ("All files", "*.*")]
        )
        root.destroy()
        if path:
            if not hasattr(self.base, 'game_config'):
                return
            bl_config = self.base.game_config.get("brainlink", {})
            bl_config["model_path"] = path
            self.base.game_config["brainlink"] = bl_config
            self._save_brainlink_config()
            logger.info(f"BrainLink model path set (load): {path}")
    
    def _brainlink_save_model(self):
        """Open file dialog to choose save location; save path to config."""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            title="Save ML model",
            defaultextension=".pkl",
            filetypes=[("Model files", "*.pkl *.joblib *.pt *.onnx"), ("All files", "*.*")]
        )
        root.destroy()
        if path:
            if not hasattr(self.base, 'game_config'):
                return
            bl_config = self.base.game_config.get("brainlink", {})
            bl_config["model_path"] = path
            self.base.game_config["brainlink"] = bl_config
            self._save_brainlink_config()
            logger.info(f"BrainLink model path set (save): {path}")
            # Ask BrainLink Client to actually save the model to this path
            if hasattr(self.base, 'input_manager') and self.base.input_manager.brainlink and self.base.input_manager.brainlink.is_connected():
                if self.base.input_manager.brainlink.send_save_model_command():
                    logger.info("Sent save model command to BrainLink Client")
                else:
                    logger.warning("Could not send save model command (BrainLink busy or not connected)")
    
    def _switch_settings_tab(self, tab_id: str):
        """Switch between settings tabs"""
        self.current_tab = tab_id
        
        # Hide all frames
        self.resolution_frame.hide()
        self.controls_frame.hide()
        self.brainlink_frame.hide()
        
        # Reset all tab button colors
        for tab_id_key, btn in self.settings_tabs.items():
            btn['frameColor'] = (0.2, 0.2, 0.3, 1)
        
        # Show selected frame and highlight tab
        if tab_id == "resolution":
            self.resolution_frame.show()
            self.settings_tabs["resolution"]['frameColor'] = (0.3, 0.3, 0.5, 1)
        elif tab_id == "controls":
            self.controls_frame.show()
            self.settings_tabs["controls"]['frameColor'] = (0.3, 0.3, 0.5, 1)
        elif tab_id == "brainlink":
            self.brainlink_frame.show()
            self.settings_tabs["brainlink"]['frameColor'] = (0.3, 0.3, 0.5, 1)
    
    def _toggle_brainlink_setting(self, key: str):
        """Toggle BrainLink setting and save to config"""
        if not hasattr(self.base, 'game_config'):
            return
        
        bl_config = self.base.game_config.get("brainlink", {})
        current_value = bl_config.get(key, False)
        new_value = not current_value
        
        # Update config
        bl_config[key] = new_value
        self.base.game_config["brainlink"] = bl_config
        
        # Update checkbox display
        checkbox = self.brainlink_checkboxes[key]
        checkbox['text'] = "✓" if new_value else " "
        checkbox['text_fg'] = (0, 1, 0, 1) if new_value else (0.5, 0.5, 0.5, 1)
        
        # Update InputManager if it exists
        if hasattr(self.base, 'input_manager'):
            if key == "send_keyboard_events":
                self.base.input_manager.send_keyboard_events = new_value
            elif key == "send_to_history":
                self.base.input_manager.send_to_history = new_value
            elif key == "send_to_ml":
                self.base.input_manager.send_to_ml = new_value
            elif key == "send_brainlink_events":
                self.base.input_manager.send_brainlink_events = new_value
        
        # Save to file
        self._save_brainlink_config()
        
        logger.info(f"BrainLink setting '{key}' changed to {new_value}")
    
    def _toggle_cheater_mode(self):
        """Toggle cheater mode (unlimited energy)"""
        if not hasattr(self.base, 'game_config'):
            return
        
        player_config = self.base.game_config.get("player", {})
        current_value = player_config.get("cheater_mode", False)
        new_value = not current_value
        
        # Update config
        player_config["cheater_mode"] = new_value
        self.base.game_config["player"] = player_config
        
        # Update checkbox display
        self.cheater_mode_checkbox['text'] = "✓" if new_value else " "
        self.cheater_mode_checkbox['text_fg'] = (0, 1, 0, 1) if new_value else (0.5, 0.5, 0.5, 1)
        
        # Update energy system if it exists
        if hasattr(self.base, 'energy_system'):
            self.base.energy_system.cheater_mode = new_value
        
        # Save to file
        self._save_game_config()
        
        logger.info(f"Cheater mode {'enabled' if new_value else 'disabled'}")
    
    def _save_brainlink_config(self):
        """Save BrainLink config to game_config.json"""
        self._save_game_config()
    
    def _save_game_config(self):
        """Save game config to game_config.json"""
        try:
            config_path = Path("config/game_config.json")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # Update all config sections
                if "brainlink" in self.base.game_config:
                    config["brainlink"] = self.base.game_config["brainlink"]
                if "player" in self.base.game_config:
                    config["player"] = self.base.game_config["player"]
                
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                
                logger.info(f"Saved game config to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save game config: {e}")

    def _on_settings_clicked(self):
        """Toggle settings panel visibility"""
        if self.settings_frame.isHidden():
            self.settings_frame.show()
            # Hide main menu buttons when settings are open to prevent overlap
            self.play_btn.hide()
            self.settings_btn.hide()
            self.quit_btn.hide()
            self.controls_text.hide()
        else:
            self.settings_frame.hide()
            # Show main menu buttons when settings are closed
            self.play_btn.show()
            self.settings_btn.show()
            self.quit_btn.show()
            self.controls_text.show()

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
        
        if self.background:
            self.background.removeNode()
        if hasattr(self, 'background_overlay') and self.background_overlay:
            self.background_overlay.removeNode()
        
        self.title.destroy()
        self.subtitle.destroy()
        self.status_frame.destroy()
        self.play_btn.destroy()
        self.quit_btn.destroy()
        self.controls_text.destroy()
