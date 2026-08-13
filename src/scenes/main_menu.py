"""Main Menu scene"""

import logging
import json
import os
import time
from pathlib import Path
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DirectEntry
from direct.gui import DirectGuiGlobals as DGG
from tkinter import filedialog
import tkinter as tk
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, CardMaker
from src.scenes.base_scene import BaseScene
from src.core.i18n import t, get_locale

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
        """Create modern gradient background for menu (aspect-correct)."""
        aspect = self.base.getAspectRatio()
        cm = CardMaker("menu_bg")
        cm.setFrame(-aspect, aspect, -1, 1)

        self.background = self.base.aspect2d.attachNewNode(cm.generate())
        self.background.setPos(0, 0, 0)
        self.background.setColor(0.08, 0.05, 0.15, 1.0)
        self.background.setTransparency(0)

        cm_overlay = CardMaker("menu_overlay")
        cm_overlay.setFrame(-aspect, aspect, -1, 1)
        overlay = self.base.aspect2d.attachNewNode(cm_overlay.generate())
        overlay.setPos(0, 0, -0.01)
        overlay.setColor(0.05, 0.03, 0.1, 0.3)
        overlay.setTransparency(1)
        self.background_overlay = overlay

        logger.debug("Menu background created (aspect2d, aspect=%.2f)", aspect)
    
    def _create_ui(self):
        """Create menu UI"""
        # Get font with Cyrillic support if available
        font = None
        if hasattr(self.base, 'cyrillic_font') and self.base.cyrillic_font:
            font = self.base.cyrillic_font
        
        # Title - properly scaled for modern resolutions
        self.title = OnscreenText(
            text=t("menu.title"),
            pos=(0, 0.65),
            scale=0.12,
            fg=(1.0, 0.9, 0.3, 1),  # Golden yellow
            shadow=(0, 0, 0, 1.0),
            shadowOffset=(0.02, 0.02),
            mayChange=True,
            font=font,
            align=TextNode.ACenter
        )
        
        # Subtitle - properly scaled
        self.subtitle = OnscreenText(
            text=t("menu.subtitle"),
            pos=(0, 0.52),
            scale=0.035,
            fg=(0.9, 0.9, 0.9, 1),
            shadow=(0, 0, 0, 0.6),
            mayChange=True,
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
            text=t("brainlink_status.label"),
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
            text=t("brainlink_status.checking"),
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
            text=t("brainlink_status.searching_info"),
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
            text=t("menu.play"),
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

        # Player name input
        player_name = (self.base.game_config.get("player", {}).get("name") or t("menu.default_player_name")) if hasattr(self.base, 'game_config') else t("menu.default_player_name")
        # Выбор игрока — на 1/6 экрана выше (z: -0.2 + 1/6*2 ≈ 0.13)
        self.player_name_label = DirectLabel(
            text=t("menu.player") + ":",
            text_scale=0.032,
            text_fg=(0.9, 0.9, 0.9, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.45, 0, 0.13),
            text_font=font,
            text_align=TextNode.ALeft
        )
        self.player_name_entry = DirectEntry(
            scale=0.032,
            initialText=(player_name[:30] if player_name else t("menu.default_player_name")),
            numLines=1,
            width=14,
            pos=(0.05, 0, 0.13),
            entryFont=DGG.getDefaultFont(),
            frameColor=(0.3, 0.35, 0.45, 1),
            borderWidth=(0.008, 0.008),
            focus=0,
            backgroundFocus=1,
            cursorKeys=1,
            command=self._apply_player_name_from_entry,
        )
        self.player_name_entry.enterText(player_name[:30] if player_name else t("menu.default_player_name"))

        self.settings_btn = DirectButton(
            text=t("menu.config"),
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
            text=t("menu.quit"),
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.2, 0.2, 1),
            frameSize=(-0.25, 0.25, -0.1, 0.1),
            pos=(0, 0, -0.7),
            command=self._on_quit_clicked,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.quit_btn, font)

        # Back to game (shown only when opened settings from pause)
        self.back_to_game_btn = DirectButton(
            text=t("menu.back_to_game"),
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.5, 0.3, 1),
            frameSize=(-0.28, 0.28, -0.1, 0.1),
            pos=(0, 0, -0.3),
            command=self._on_back_to_game_clicked,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.back_to_game_btn, font)
        self.back_to_game_btn.hide()
        
        # Controls info - properly scaled, positioned just below Quit button
        self.controls_text = OnscreenText(
            text=t("menu.controls_hint"),
            pos=(0, -0.85),
            scale=0.028,
            fg=(0.7, 0.7, 0.7, 1),
            shadow=(0, 0, 0, 0.5),
            mayChange=True,
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
        self.back_to_game_btn.hide()
        if hasattr(self, 'player_name_label'):
            self.player_name_label.hide()
        if hasattr(self, 'player_name_entry'):
            self.player_name_entry.hide()
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
        self._update_from_pause_buttons()
        if hasattr(self, 'player_name_label'):
            self.player_name_label.show()
        if hasattr(self, 'player_name_entry'):
            self.player_name_entry.show()
        self.settings_btn.show()
        self.quit_btn.show()
        self.controls_text.show()
        # Settings frame stays hidden unless opened

    def _update_from_pause_buttons(self):
        """Show Play or Back to game depending on whether we came from pause."""
        if getattr(self.base, "_from_pause_settings", False):
            self.play_btn.hide()
            self.back_to_game_btn.show()
        else:
            self.play_btn.show()
            self.back_to_game_btn.hide()

    def _on_back_to_game_clicked(self):
        """Return to game without reset (called when opened settings from pause)."""
        if hasattr(self.base, "_return_from_settings_to_game"):
            self.base._return_from_settings_to_game()

    def _apply_player_name_from_entry(self, *args, **kwargs):
        """Save player name from main menu input field."""
        if not hasattr(self, "player_name_entry"):
            return
        new_name = (self.player_name_entry.get() or "").strip()[:30] or t("menu.default_player_name")
        self.player_name_entry.enterText(new_name)
        if hasattr(self.base, 'game_config'):
            self.base.game_config.setdefault("player", {})["name"] = new_name
            self._save_game_config()
        logger.info("Player name set: %s", new_name)
    
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
            text=t("settings.title"),
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
        
        # Close button — на 1/6 экрана ниже (aspect2d: ~0.17 вниз)
        self.settings_close_btn = DirectButton(
            text=t("settings.close"),
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.5, 0.2, 0.2, 1),
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            pos=(0, 0, -0.62),
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
            (t("settings.tab_resolution"), "resolution", -0.45),
            (t("settings.tab_controls"), "controls", -0.05),
            (t("settings.tab_brainlink"), "brainlink", 0.35)
        ]
        
        self._tab_label_keys = {
            "resolution": "settings.tab_resolution",
            "controls": "settings.tab_controls",
            "brainlink": "settings.tab_brainlink",
        }
        
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

        fullscreen = False
        if hasattr(self.base, "game_config"):
            fullscreen = bool(self.base.game_config.get("window", {}).get("fullscreen", False))

        self.resolution_status_label = DirectLabel(
            text=self._resolution_status_text(),
            text_scale=0.028,
            text_fg=(0.85, 0.85, 0.95, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.2),
            parent=self.resolution_frame,
            text_font=font,
            text_align=TextNode.ACenter,
        )

        self.resolution_resolution_label = DirectLabel(
            text=t("settings.resolution"),
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, 0.12),
            parent=self.resolution_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )

        self.resolution_buttons = {}

        def add_resolution_button(text, width, height, z):
            btn = DirectButton(
                text=text,
                text_scale=0.03,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.25, 0.25, 0.35, 1),
                frameSize=(-0.45, 0.45, -0.045, 0.045),
                pos=(0, 0, z),
                command=self._apply_resolution_preset,
                extraArgs=[width, height],
                parent=self.resolution_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.005, 0.005),
            )
            if font:
                self._apply_font_to_button(btn, font)
            self.resolution_buttons[(width, height)] = btn
            return btn

        self.btn_res_1280 = add_resolution_button("1280 x 720", 1280, 720, 0.03)
        self.btn_res_1600 = add_resolution_button("1600 x 900", 1600, 900, -0.07)
        self.btn_res_1920 = add_resolution_button("1920 x 1080", 1920, 1080, -0.17)

        self.resolution_fullscreen_label = DirectLabel(
            text=t("settings.fullscreen"),
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.45, 0, -0.28),
            parent=self.resolution_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        self.fullscreen_checkbox = DirectButton(
            text="+" if fullscreen else "",
            text_scale=0.05,
            text_fg=(0.9, 1, 0.9, 1) if fullscreen else (0.5, 0.5, 0.5, 1),
            frameColor=(0.15, 0.4, 0.2, 1) if fullscreen else (0.22, 0.22, 0.28, 1),
            frameSize=(-0.055, 0.055, -0.045, 0.045),
            pos=(0.35, 0, -0.28),
            command=self._toggle_fullscreen_setting,
            parent=self.resolution_frame,
            text_font=font,
            relief=2,
            borderWidth=(0.008, 0.008),
        )

        self.apply_display_btn = DirectButton(
            text=t("settings.apply_display"),
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.14, 0.14, -0.04, 0.04),
            pos=(0, 0, -0.38),
            command=self._apply_current_display_settings,
            parent=self.resolution_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003),
        )

        self._refresh_resolution_ui()

    def _resolution_status_text(self) -> str:
        if hasattr(self.base, "get_window_display_info"):
            return t("settings.current", info=self.base.get_window_display_info())
        cfg = getattr(self.base, "game_config", {}).get("window", {})
        info = f"{cfg.get('width', '?')} x {cfg.get('height', '?')}"
        return t("settings.current", info=info)

    def _refresh_resolution_ui(self):
        """Highlight active resolution preset and refresh status label."""
        if hasattr(self, "resolution_status_label"):
            self.resolution_status_label["text"] = self._resolution_status_text()
        cfg = getattr(self.base, "game_config", {}).get("window", {})
        current = (int(cfg.get("width", 0)), int(cfg.get("height", 0)))
        active_color = (0.3, 0.45, 0.55, 1)
        idle_color = (0.25, 0.25, 0.35, 1)
        for (w, h), btn in getattr(self, "resolution_buttons", {}).items():
            btn["frameColor"] = active_color if (w, h) == current else idle_color
        fs = bool(cfg.get("fullscreen", False))
        if hasattr(self, "fullscreen_checkbox"):
            self.fullscreen_checkbox["text"] = "+" if fs else ""
            self.fullscreen_checkbox["text_fg"] = (0.9, 1, 0.9, 1) if fs else (0.5, 0.5, 0.5, 1)
            self.fullscreen_checkbox["frameColor"] = (0.15, 0.4, 0.2, 1) if fs else (0.22, 0.22, 0.28, 1)

    def _is_fullscreen_enabled(self) -> bool:
        if hasattr(self, "fullscreen_checkbox"):
            return bool(self.fullscreen_checkbox["text"])
        return bool(getattr(self.base, "game_config", {}).get("window", {}).get("fullscreen", False))

    def _toggle_fullscreen_setting(self):
        enabled = self._is_fullscreen_enabled()
        self.fullscreen_checkbox["text"] = "" if enabled else "+"
        self.fullscreen_checkbox["text_fg"] = (0.5, 0.5, 0.5, 1) if enabled else (0.9, 1, 0.9, 1)
        self.fullscreen_checkbox["frameColor"] = (0.22, 0.22, 0.28, 1) if enabled else (0.15, 0.4, 0.2, 1)

    def _apply_resolution_preset(self, width: int, height: int):
        """Apply selected windowed resolution or native fullscreen size."""
        self._apply_resolution(width, height, self._is_fullscreen_enabled())

    def _apply_current_display_settings(self):
        """Re-apply current preset + fullscreen checkbox."""
        cfg = getattr(self.base, "game_config", {}).get("window", {})
        width = int(cfg.get("width", 1920))
        height = int(cfg.get("height", 1080))
        self._apply_resolution(width, height, self._is_fullscreen_enabled())
    
    def _create_controls_tab(self, font):
        """Create controls settings tab with cheater mode and keyboard rebind"""
        self.controls_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.55, 0.55, -0.52, 0.25),
            pos=(0, 0, 0.05),
            parent=self.settings_frame
        )
        
        # Get current cheater mode setting
        cheater_mode = False
        if hasattr(self.base, 'game_config'):
            cheater_mode = self.base.game_config.get("player", {}).get("cheater_mode", False)
        
        # Cheater Mode checkbox
        self.cheater_mode_label = DirectLabel(
            text=t("settings.cheater_mode"),
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.4, 0, 0.1),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        
        self.cheater_mode_hint = DirectLabel(
            text=t("settings.cheater_hint"),
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
        
        # Keyboard layout: movement + sit + sit+pause
        default_keys = {"up": "arrow_up", "down": "arrow_down", "left": "arrow_left", "right": "arrow_right", "action": "space", "sit_pause": "p"}
        controls_cfg = self.base.game_config.get("controls", {}).get("keyboard", default_keys) if hasattr(self.base, "game_config") else default_keys
        key_labels = [
            ("settings.key_up", "up"),
            ("settings.key_down", "down"),
            ("settings.key_left", "left"),
            ("settings.key_right", "right"),
            ("settings.key_sit", "action"),
            ("settings.key_sit_pause", "sit_pause"),
        ]
        self.controls_key_buttons = {}
        self.controls_action_labels = {}
        for i, (label_key, action) in enumerate(key_labels):
            z = 0.05 - (i + 1) * 0.08
            lbl = DirectLabel(
                text=t(label_key) + ":",
                text_scale=0.032,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(-0.45, 0, z),
                parent=self.controls_frame,
                text_font=font,
                text_align=TextNode.ALeft
            )
            self.controls_action_labels[action] = (lbl, label_key)
            key_name = controls_cfg.get(action, default_keys.get(action, "?"))
            btn = DirectButton(
                text=self._key_display_name(key_name),
                text_scale=0.028,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.25, 0.25, 0.4, 1),
                frameSize=(-0.2, 0.2, -0.035, 0.035),
                pos=(0.15, 0, z),
                command=self._start_rebind_key,
                extraArgs=[action],
                parent=self.controls_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.004, 0.004)
            )
            self.controls_key_buttons[action] = btn
        
        current_locale = getattr(self.base, "game_config", {}).get("locale", get_locale())
        self.language_label = DirectLabel(
            text=t("settings.language"),
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.45, 0, -0.48),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        active_lang = (0.3, 0.5, 0.35, 1)
        idle_lang = (0.25, 0.25, 0.35, 1)
        self.lang_btn_en = DirectButton(
            text=t("settings.lang_en"),
            text_scale=0.028,
            text_fg=(1, 1, 1, 1),
            frameColor=active_lang if current_locale == "en" else idle_lang,
            frameSize=(-0.12, 0.12, -0.035, 0.035),
            pos=(0.05, 0, -0.48),
            command=self._set_language,
            extraArgs=["en"],
            parent=self.controls_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.004, 0.004),
        )
        self.lang_btn_ru = DirectButton(
            text=t("settings.lang_ru"),
            text_scale=0.028,
            text_fg=(1, 1, 1, 1),
            frameColor=active_lang if current_locale == "ru" else idle_lang,
            frameSize=(-0.12, 0.12, -0.035, 0.035),
            pos=(0.28, 0, -0.48),
            command=self._set_language,
            extraArgs=["ru"],
            parent=self.controls_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.004, 0.004),
        )
        
        self._rebind_action = None
        self.REBIND_KEYS = [
            "arrow_up", "arrow_down", "arrow_left", "arrow_right",
            "space", "w", "a", "s", "d", "p", "r", "t", "f", "g", "e", "q", "z", "x", "c", "v", "b", "n", "m",
            "return", "backspace", "tab", "shift", "control", "alt",
            "numpad2", "numpad4", "numpad6", "numpad8",
        ]
    
    def _key_display_name(self, key_name: str) -> str:
        """Human-readable key name for display."""
        if not key_name:
            return "?"
        s = key_name.replace("arrow_", "").replace("-", " ").strip()
        return s[:1].upper() + s[1:] if s else key_name
    
    def _start_rebind_key(self, action: str):
        """Start listening for next key press to rebind."""
        if self._rebind_action:
            return
        self._rebind_action = action
        btn = self.controls_key_buttons.get(action)
        if btn:
            btn["text"] = t("settings.rebind_wait")
        for key in self.REBIND_KEYS:
            self.base.accept(key, self._on_rebind_key, [key])
    
    def _on_rebind_key(self, key_name: str):
        """Assign key to current action and stop listening."""
        if not self._rebind_action:
            return
        action = self._rebind_action
        self._rebind_action = None
        for key in self.REBIND_KEYS:
            self.base.ignore(key)
        
        if not hasattr(self.base, "game_config"):
            return
        ctrl = self.base.game_config.get("controls", {})
        kbd = ctrl.get("keyboard", {})
        kbd[action] = key_name
        ctrl["keyboard"] = kbd
        self.base.game_config["controls"] = ctrl
        
        try:
            config_path = Path("config/game_config.json")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                config.setdefault("controls", {})["keyboard"] = kbd
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save key config: %s", e)
        
        if hasattr(self.base, "input_manager") and self.base.input_manager:
            self.base.input_manager.rebind_keys()
        
        btn = self.controls_key_buttons.get(action)
        if btn:
            btn["text"] = self._key_display_name(key_name)
        logger.info("Key bound: %s -> %s", action, key_name)
    
    def _create_brainlink_tab(self, font):
        """Create BrainLink settings tab"""
        self.brainlink_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.55, 0.55, -0.56, 0.25),
            pos=(0, 0, 0.05),
            parent=self.settings_frame
        )
        
        # Get current BrainLink config
        bl_config = {}
        if hasattr(self.base, 'game_config'):
            bl_config = self.base.game_config.get("brainlink", {})
        
        # BrainLink settings checkboxes (same style as other tabs: button as checkbox)
        settings = [
            ("settings.bl_send_keyboard", "send_keyboard_events", 0.15, bl_config.get("send_keyboard_events", True)),
            ("settings.bl_send_history", "send_to_history", 0.05, bl_config.get("send_to_history", True)),
            ("settings.bl_send_ml", "send_to_ml", -0.05, bl_config.get("send_to_ml", True)),
            ("settings.bl_send_events", "send_brainlink_events", -0.15, bl_config.get("send_brainlink_events", True)),
        ]
        
        self.brainlink_checkboxes = {}
        self.brainlink_setting_labels = {}
        for label_key, key, z_pos, default_value in settings:
            lbl = DirectLabel(
                text=t(label_key) + ":",
                text_scale=0.035,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(-0.4, 0, z_pos),
                parent=self.brainlink_frame,
                text_font=font,
                text_align=TextNode.ALeft
            )
            self.brainlink_setting_labels[key] = (lbl, label_key)
            
            checkbox = DirectButton(
                text="+" if default_value else "",
                text_scale=0.05,
                text_fg=(0.9, 1, 0.9, 1) if default_value else (0.5, 0.5, 0.5, 1),
                frameColor=(0.15, 0.4, 0.2, 1) if default_value else (0.22, 0.22, 0.28, 1),
                frameSize=(-0.055, 0.055, -0.045, 0.045),
                pos=(0.35, 0, z_pos),
                command=self._toggle_brainlink_setting,
                extraArgs=[key],
                parent=self.brainlink_frame,
                text_font=font,
                relief=2,
                borderWidth=(0.008, 0.008)
            )
            self.brainlink_checkboxes[key] = checkbox
        
        # Numeric settings — always-visible input fields
        entry_font = DGG.getDefaultFont()
        _entry_color = (0.28, 0.32, 0.45, 1)

        def _float_fmt(x):
            return f"{float(x):.2f}"

        def _float_parse(s):
            return float(s.strip().replace(",", "."))

        def _make_field_command(key):
            def _cmd(*_args):
                self._brainlink_apply_single_field(key)
            return _cmd

        self.brainlink_field_labels = {}

        def _config_entry_row(label_key, z_pos, config_key, default_val, width=8):
            val = bl_config.get(config_key, default_val)
            text = _float_fmt(val)
            lbl = DirectLabel(
                text=t(label_key),
                text_scale=0.032,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(-0.4, 0, z_pos),
                parent=self.brainlink_frame,
                text_font=font,
                text_align=TextNode.ALeft,
            )
            self.brainlink_field_labels[config_key] = (lbl, label_key)
            entry = DirectEntry(
                parent=self.brainlink_frame,
                scale=0.04,
                pos=(0.08, 0, z_pos),
                width=width,
                numLines=1,
                initialText=text,
                entryFont=entry_font,
                frameColor=_entry_color,
                borderWidth=(0.008, 0.008),
                focus=0,
                backgroundFocus=0,
                cursorKeys=1,
                command=_make_field_command(config_key),
                focusInCommand=self._brainlink_entry_focus_in,
                focusInExtraArgs=[config_key],
                focusOutCommand=self._brainlink_entry_focus_out,
                focusOutExtraArgs=[config_key],
            )
            entry.enterText(text)
            return entry

        self._brainlink_cached_values = {
            "confidence_threshold": _float_fmt(bl_config.get("confidence_threshold", 0.5)),
            "min_confidence": _float_fmt(bl_config.get("min_confidence", 0.25)),
            "full_confidence": _float_fmt(bl_config.get("full_confidence", 0.7)),
        }
        self._brainlink_active_field = None
        self._brainlink_weights_active = False

        self.brainlink_entries = {
            "confidence_threshold": {
                "entry": _config_entry_row("settings.bl_conf_threshold", -0.26, "confidence_threshold", 0.5),
                "default": 0.5,
                "parse": _float_parse,
                "fmt": _float_fmt,
                "clamp": (0.0, 1.0),
            },
            "min_confidence": {
                "entry": _config_entry_row("settings.bl_min_confidence", -0.32, "min_confidence", 0.25),
                "default": 0.25,
                "parse": _float_parse,
                "fmt": _float_fmt,
                "clamp": (0.0, 1.0),
            },
            "full_confidence": {
                "entry": _config_entry_row("settings.bl_full_confidence", -0.38, "full_confidence", 0.7),
                "default": 0.7,
                "parse": _float_parse,
                "fmt": _float_fmt,
                "clamp": (0.0, 1.0),
            },
        }

        weights = bl_config.get("prediction_weights", [1.0, 1.0, 1.0, 1.0])
        weights_str = ", ".join(str(round(w, 2)) for w in (weights + [1.0] * 4)[:4])

        self.brainlink_weights_label = DirectLabel(
            text=t("settings.bl_weights"),
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.4, 0, -0.44),
            parent=self.brainlink_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )

        self._brainlink_cached_weights = weights_str

        self.brainlink_weights_entry = DirectEntry(
            parent=self.brainlink_frame,
            scale=0.038,
            pos=(0.05, 0, -0.44),
            width=20,
            numLines=1,
            initialText=weights_str,
            entryFont=entry_font,
            frameColor=_entry_color,
            borderWidth=(0.008, 0.008),
            focus=0,
            backgroundFocus=0,
            cursorKeys=1,
            command=self._brainlink_apply_weights_field,
            focusInCommand=self._brainlink_weights_focus_in,
            focusOutCommand=self._brainlink_weights_focus_out,
        )
        self.brainlink_weights_entry.enterText(weights_str)

        self.brainlink_apply_btn = DirectButton(
            text=t("settings.apply"),
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.08, 0.08, -0.04, 0.04),
            pos=(0.48, 0, -0.40),
            command=self._brainlink_apply_ml_config,
            parent=self.brainlink_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )

        # Load / Save model buttons
        self.brainlink_load_model_btn = DirectButton(
            text=t("settings.load_model"),
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.25, 0.4, 1),
            frameSize=(-0.12, 0.12, -0.04, 0.04),
            pos=(-0.2, 0, -0.52),
            command=self._brainlink_load_model,
            parent=self.brainlink_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )
        self.brainlink_save_model_btn = DirectButton(
            text=t("settings.save_model"),
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.12, 0.12, -0.04, 0.04),
            pos=(0.2, 0, -0.52),
            command=self._brainlink_save_model,
            parent=self.brainlink_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.003, 0.003)
        )
    
    def _brainlink_entry_focus_in(self, key):
        """Only one BrainLink field receives keyboard input at a time."""
        self._brainlink_active_field = key
        self._brainlink_weights_active = False
        for k, meta in getattr(self, "brainlink_entries", {}).items():
            if k != key:
                meta["entry"]["focus"] = 0

    def _brainlink_entry_focus_out(self, key):
        """Remember field text when focus leaves."""
        meta = getattr(self, "brainlink_entries", {}).get(key)
        if meta:
            self._brainlink_cached_values[key] = meta["entry"].get(plain=True).strip()
        if getattr(self, "_brainlink_active_field", None) == key:
            self._brainlink_active_field = None

    def _brainlink_weights_focus_in(self):
        self._brainlink_weights_active = True
        self._brainlink_active_field = None
        for meta in getattr(self, "brainlink_entries", {}).values():
            meta["entry"]["focus"] = 0

    def _brainlink_weights_focus_out(self):
        if hasattr(self, "brainlink_weights_entry"):
            self._brainlink_cached_weights = self.brainlink_weights_entry.get(plain=True).strip()
        self._brainlink_weights_active = False

    def _brainlink_sync_active_field_to_cache(self):
        """Copy currently focused field into cache before bulk apply."""
        active = getattr(self, "_brainlink_active_field", None)
        if active and active in getattr(self, "brainlink_entries", {}):
            entry = self.brainlink_entries[active]["entry"]
            self._brainlink_cached_values[active] = entry.get(plain=True).strip()
        if getattr(self, "_brainlink_weights_active", False) and hasattr(self, "brainlink_weights_entry"):
            self._brainlink_cached_weights = self.brainlink_weights_entry.get(plain=True).strip()

    def _brainlink_apply_single_field(self, key):
        """Apply one numeric BrainLink field (Enter in that input)."""
        if not hasattr(self.base, "game_config") or key not in getattr(self, "brainlink_entries", {}):
            return
        meta = self.brainlink_entries[key]
        bl_config = self.base.game_config.get("brainlink", {})
        text = meta["entry"].get(plain=True).strip() or self._brainlink_cached_values.get(key, "")
        fallback = bl_config.get(key, meta["default"])
        try:
            val = meta["parse"](text)
            if meta.get("clamp"):
                lo, hi = meta["clamp"]
                val = max(lo, min(hi, val))
            formatted = meta["fmt"](val)
            bl_config[key] = val
            self.base.game_config["brainlink"] = bl_config
            meta["entry"].enterText(formatted)
            self._brainlink_cached_values[key] = formatted
            self._save_brainlink_config()
            logger.info("BrainLink config updated: %s = %s", key, val)
        except (ValueError, TypeError) as e:
            logger.warning("Invalid %s: %s", key, e)
            restored = meta["fmt"](fallback)
            meta["entry"].enterText(restored)
            self._brainlink_cached_values[key] = restored

    def _brainlink_apply_weights_field(self, *args, **kwargs):
        """Apply weights field only (Enter in weights input)."""
        if not hasattr(self.base, "game_config") or not hasattr(self, "brainlink_weights_entry"):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        fallback_weights = bl_config.get("prediction_weights", [1.0, 1.0, 1.0, 1.0])
        text = self.brainlink_weights_entry.get(plain=True).strip() or getattr(
            self, "_brainlink_cached_weights", ""
        )
        try:
            parts = [p.strip().replace(",", ".") for p in text.split(",")]
            vals = [float(x) for x in parts[:4]]
            if len(vals) < 4:
                vals.extend([1.0] * (4 - len(vals)))
            formatted = ", ".join(str(round(x, 2)) for x in vals[:4])
            bl_config["prediction_weights"] = vals[:4]
            self.base.game_config["brainlink"] = bl_config
            self.brainlink_weights_entry.enterText(formatted)
            self._brainlink_cached_weights = formatted
            self._save_brainlink_config()
            logger.info("BrainLink weights updated: %s", vals[:4])
        except (ValueError, TypeError) as e:
            logger.warning("Invalid weights: %s", e)
            restored = ", ".join(str(round(w, 2)) for w in (fallback_weights + [1.0] * 4)[:4])
            self.brainlink_weights_entry.enterText(restored)
            self._brainlink_cached_weights = restored

    def _refresh_brainlink_entries_from_config(self):
        """Reload BrainLink input fields from current game config."""
        if not hasattr(self, "brainlink_entries") or not hasattr(self.base, "game_config"):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        if not hasattr(self, "_brainlink_cached_values"):
            self._brainlink_cached_values = {}
        for key, meta in self.brainlink_entries.items():
            val = bl_config.get(key, meta["default"])
            formatted = meta["fmt"](val)
            meta["entry"].enterText(formatted)
            self._brainlink_cached_values[key] = formatted
        weights = bl_config.get("prediction_weights", [1.0, 1.0, 1.0, 1.0])
        weights_str = ", ".join(str(round(w, 2)) for w in (weights + [1.0] * 4)[:4])
        if hasattr(self, "brainlink_weights_entry"):
            self.brainlink_weights_entry.enterText(weights_str)
            self._brainlink_cached_weights = weights_str

    def _brainlink_apply_ml_config(self, *args, **kwargs):
        """Read all BrainLink input fields from cache, validate, save."""
        if not hasattr(self.base, 'game_config'):
            return
        self._brainlink_sync_active_field_to_cache()
        bl_config = self.base.game_config.get("brainlink", {})
        ok = True

        for key, meta in getattr(self, "brainlink_entries", {}).items():
            text = self._brainlink_cached_values.get(key, "").strip()
            fallback = bl_config.get(key, meta["default"])
            if not text:
                text = meta["fmt"](fallback)
            try:
                val = meta["parse"](text)
                if meta.get("clamp"):
                    lo, hi = meta["clamp"]
                    val = max(lo, min(hi, val))
                formatted = meta["fmt"](val)
                bl_config[key] = val
                meta["entry"].enterText(formatted)
                self._brainlink_cached_values[key] = formatted
            except (ValueError, TypeError) as e:
                logger.warning("Invalid %s: %s", key, e)
                restored = meta["fmt"](fallback)
                meta["entry"].enterText(restored)
                self._brainlink_cached_values[key] = restored
                ok = False

        if hasattr(self, "brainlink_weights_entry"):
            text = getattr(self, "_brainlink_cached_weights", "").strip()
            fallback_weights = bl_config.get("prediction_weights", [1.0, 1.0, 1.0, 1.0])
            if not text:
                text = ", ".join(str(round(w, 2)) for w in (fallback_weights + [1.0] * 4)[:4])
            try:
                parts = [p.strip().replace(",", ".") for p in text.split(",")]
                vals = [float(x) for x in parts[:4]]
                if len(vals) < 4:
                    vals.extend([1.0] * (4 - len(vals)))
                formatted = ", ".join(str(round(x, 2)) for x in vals[:4])
                bl_config["prediction_weights"] = vals[:4]
                self.brainlink_weights_entry.enterText(formatted)
                self._brainlink_cached_weights = formatted
            except (ValueError, TypeError) as e:
                logger.warning("Invalid weights: %s", e)
                restored = ", ".join(str(round(w, 2)) for w in (fallback_weights + [1.0] * 4)[:4])
                self.brainlink_weights_entry.enterText(restored)
                self._brainlink_cached_weights = restored
                ok = False

        self.base.game_config["brainlink"] = bl_config
        self._save_brainlink_config()
        if ok:
            logger.info("BrainLink ML config applied")
    
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
        """Open file dialog to choose save location; save path to config; ask BrainLink to save model."""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            title="Save ML model",
            defaultextension=".pkl",
            filetypes=[("Pickle model", "*.pkl"), ("Model files", "*.pkl *.joblib *.pt *.onnx"), ("All files", "*.*")]
        )
        root.destroy()
        if path:
            if not hasattr(self.base, 'game_config'):
                return
            # Use absolute path so BrainLink Client can save to the same path
            path_abs = str(Path(path).resolve())
            bl_config = self.base.game_config.get("brainlink", {})
            bl_config["model_path"] = path_abs
            self.base.game_config["brainlink"] = bl_config
            self._save_brainlink_config()
            logger.info(f"BrainLink model path set (save): {path_abs}")
            # Записать путь к game_config.json в известный файл, чтобы BrainLink мог прочитать конфиг даже без --game-config
            _game_config_path = Path("config/game_config.json").resolve()
            _brainlink_config_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "BrainLink"
            _brainlink_config_dir.mkdir(parents=True, exist_ok=True)
            (_brainlink_config_dir / "game_config_path.txt").write_text(str(_game_config_path), encoding="utf-8")
            # Ensure config is written to disk before client reads it
            time.sleep(0.15)
            if hasattr(self.base, 'input_manager') and self.base.input_manager.brainlink and self.base.input_manager.brainlink.is_connected():
                if self.base.input_manager.brainlink.send_save_model_command():
                    logger.info("Sent save model command to BrainLink Client")
                else:
                    logger.warning("Could not send save model command (BrainLink busy or not connected)")
            else:
                logger.warning("BrainLink not connected — start BrainLink Client to save the model.")
    
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
            self._refresh_resolution_ui()
        elif tab_id == "controls":
            self.controls_frame.show()
            self.settings_tabs["controls"]['frameColor'] = (0.3, 0.3, 0.5, 1)
        elif tab_id == "brainlink":
            self.brainlink_frame.show()
            self.settings_tabs["brainlink"]['frameColor'] = (0.3, 0.3, 0.5, 1)
            self._refresh_brainlink_entries_from_config()
    
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
        checkbox['text'] = "+" if new_value else ""
        checkbox['text_fg'] = (0.9, 1, 0.9, 1) if new_value else (0.5, 0.5, 0.5, 1)
        checkbox['frameColor'] = (0.15, 0.4, 0.2, 1) if new_value else (0.22, 0.22, 0.28, 1)
        
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
    
    def _set_language(self, locale: str):
        """Switch UI language."""
        if hasattr(self.base, "set_locale"):
            self.base.set_locale(locale)
        self._refresh_language_buttons()
    
    def _refresh_language_buttons(self):
        locale = getattr(self.base, "game_config", {}).get("locale", get_locale())
        active = (0.3, 0.5, 0.35, 1)
        idle = (0.25, 0.25, 0.35, 1)
        if hasattr(self, "lang_btn_en"):
            self.lang_btn_en["frameColor"] = active if locale == "en" else idle
        if hasattr(self, "lang_btn_ru"):
            self.lang_btn_ru["frameColor"] = active if locale == "ru" else idle
    
    def refresh_locale(self):
        """Update all menu/settings strings after language change."""
        self.title.setText(t("menu.title"))
        self.subtitle.setText(t("menu.subtitle"))
        self.brainlink_status_label["text"] = t("brainlink_status.label")
        self.play_btn["text"] = t("menu.play")
        self.player_name_label["text"] = t("menu.player") + ":"
        self.settings_btn["text"] = t("menu.config")
        self.quit_btn["text"] = t("menu.quit")
        self.back_to_game_btn["text"] = t("menu.back_to_game")
        self.controls_text.setText(t("menu.controls_hint"))
        self.settings_title["text"] = t("settings.title")
        self.settings_close_btn["text"] = t("settings.close")
        for tab_id, btn in getattr(self, "settings_tabs", {}).items():
            key = getattr(self, "_tab_label_keys", {}).get(tab_id)
            if key:
                btn["text"] = t(key)
        if hasattr(self, "resolution_resolution_label"):
            self.resolution_resolution_label["text"] = t("settings.resolution")
        if hasattr(self, "resolution_fullscreen_label"):
            self.resolution_fullscreen_label["text"] = t("settings.fullscreen")
        if hasattr(self, "apply_display_btn"):
            self.apply_display_btn["text"] = t("settings.apply_display")
        self._refresh_resolution_ui()
        if hasattr(self, "cheater_mode_label"):
            self.cheater_mode_label["text"] = t("settings.cheater_mode")
        if hasattr(self, "cheater_mode_hint"):
            self.cheater_mode_hint["text"] = t("settings.cheater_hint")
        for action, (lbl, key) in getattr(self, "controls_action_labels", {}).items():
            lbl["text"] = t(key) + ":"
        if hasattr(self, "language_label"):
            self.language_label["text"] = t("settings.language")
        if hasattr(self, "lang_btn_en"):
            self.lang_btn_en["text"] = t("settings.lang_en")
        if hasattr(self, "lang_btn_ru"):
            self.lang_btn_ru["text"] = t("settings.lang_ru")
        self._refresh_language_buttons()
        for key, (lbl, label_key) in getattr(self, "brainlink_setting_labels", {}).items():
            lbl["text"] = t(label_key) + ":"
        for config_key, (lbl, label_key) in getattr(self, "brainlink_field_labels", {}).items():
            lbl["text"] = t(label_key)
        if hasattr(self, "brainlink_weights_label"):
            self.brainlink_weights_label["text"] = t("settings.bl_weights")
        if hasattr(self, "brainlink_apply_btn"):
            self.brainlink_apply_btn["text"] = t("settings.apply")
        if hasattr(self, "brainlink_load_model_btn"):
            self.brainlink_load_model_btn["text"] = t("settings.load_model")
        if hasattr(self, "brainlink_save_model_btn"):
            self.brainlink_save_model_btn["text"] = t("settings.save_model")
    
    def _save_brainlink_config(self):
        """Save BrainLink config to game_config.json"""
        self._save_game_config()
    
    def _save_game_config(self):
        """Save game config to game_config.json (create file and dir if missing)."""
        try:
            config_path = Path("config/game_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            # Merge in current in-memory config
            if "brainlink" in self.base.game_config:
                config["brainlink"] = self.base.game_config["brainlink"]
            if "player" in self.base.game_config:
                config["player"] = self.base.game_config["player"]
            if "controls" in self.base.game_config:
                config["controls"] = self.base.game_config["controls"]
            if "window" in self.base.game_config:
                config["window"] = self.base.game_config["window"]
            if "locale" in self.base.game_config:
                config["locale"] = self.base.game_config["locale"]
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved game config to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save game config: {e}")

    def _on_settings_clicked(self):
        """Toggle settings panel visibility"""
        if self.settings_frame.isHidden():
            self.settings_frame.show()
            self._refresh_brainlink_entries_from_config()
            self._refresh_resolution_ui()
            # Hide main menu buttons when settings are open to prevent overlap
            self.play_btn.hide()
            self.back_to_game_btn.hide()
            self.settings_btn.hide()
            self.quit_btn.hide()
            self.controls_text.hide()
        else:
            self._brainlink_apply_ml_config()
            self.settings_frame.hide()
            # If we came from pause, return to game; else show main menu buttons
            if getattr(self.base, "_from_pause_settings", False):
                if hasattr(self.base, "_return_from_settings_to_game"):
                    self.base._return_from_settings_to_game()
                return
            self._update_from_pause_buttons()
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
            self._refresh_resolution_ui()
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
