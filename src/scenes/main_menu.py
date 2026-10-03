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
from src.services.brainlink_config_sync import sync_brainlink_config_from_client

logger = logging.getLogger(__name__)

BRAINLINK_BASE_FAULT_FIELDS = (
    "attention", "meditation", "signal", "delta", "theta",
    "low_alpha", "high_alpha", "low_beta", "high_beta", "low_gamma", "high_gamma",
)

DEFAULT_BASE_FAULT = {
    "attention": 5,
    "meditation": 10,
    "signal": 0,
    "delta": 300,
    "theta": 300,
    "low_alpha": 0,
    "high_alpha": 0,
    "low_beta": 0,
    "high_beta": 0,
    "low_gamma": 0,
    "high_gamma": 0,
}

DEFAULT_MULTI_FAULT = {
    "attention": 1,
    "meditation": 1,
    "signal": 1,
    "delta": 3,
    "theta": 3,
    "low_alpha": 3,
    "high_alpha": 3,
    "low_beta": 3,
    "high_beta": 3,
    "low_gamma": 3,
    "high_gamma": 3,
}

DEFAULT_MULTI_COUNT = 1


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
        
        # Main menu buttons: compact height + fixed vertical gap (no overlap)
        _menu_btn_w = 0.25
        _menu_btn_h = 0.045
        _menu_btn_step = _menu_btn_h * 2 + 0.02
        _menu_play_z = -0.28
        _menu_settings_z = _menu_play_z - _menu_btn_step
        _menu_brainlink_z = _menu_settings_z - _menu_btn_step
        _menu_quit_z = _menu_brainlink_z - _menu_btn_step
        _menu_btn_frame = (-_menu_btn_w, _menu_btn_w, -_menu_btn_h, _menu_btn_h)

        self.play_btn = DirectButton(
            text=t("menu.play"),
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.6, 0.2, 1),
            frameSize=_menu_btn_frame,
            pos=(0, 0, _menu_play_z),
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
            text_scale=0.028,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.6, 1),
            frameSize=_menu_btn_frame,
            pos=(0, 0, _menu_settings_z),
            command=self._on_settings_clicked,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.settings_btn, font)

        self.brainlink_settings_btn = DirectButton(
            text=t("menu.brainlink_settings"),
            text_scale=0.024,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.45, 0.55, 1),
            frameSize=_menu_btn_frame,
            pos=(0, 0, _menu_brainlink_z),
            command=self._on_brainlink_settings_clicked,
            text_font=font,
        )
        if font:
            self._apply_font_to_button(self.brainlink_settings_btn, font)
        
        # Quit button
        self.quit_btn = DirectButton(
            text=t("menu.quit"),
            text_scale=0.032,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.2, 0.2, 1),
            frameSize=_menu_btn_frame,
            pos=(0, 0, _menu_quit_z),
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
            frameSize=_menu_btn_frame,
            pos=(0, 0, _menu_play_z),
            command=self._on_back_to_game_clicked,
            text_font=font
        )
        if font:
            self._apply_font_to_button(self.back_to_game_btn, font)
        self.back_to_game_btn.hide()
        
        # Controls info - properly scaled, positioned just below Quit button
        self.controls_text = OnscreenText(
            text=t("menu.controls_hint"),
            pos=(0, _menu_quit_z - _menu_btn_h - 0.08),
            scale=0.028,
            fg=(0.7, 0.7, 0.7, 1),
            shadow=(0, 0, 0, 0.5),
            mayChange=True,
            font=font,
            align=TextNode.ACenter
        )

        # Settings panels (hidden by default)
        self._create_settings_panel(font)
        self._create_brainlink_settings_panel(font)
        
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
        if hasattr(self, "brainlink_settings_btn"):
            self.brainlink_settings_btn.hide()
        self.quit_btn.hide()
        self.controls_text.hide()
        if hasattr(self, 'settings_frame'):
            self.settings_frame.hide()
        if hasattr(self, 'brainlink_settings_frame'):
            self.brainlink_settings_frame.hide()
    
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
        if hasattr(self, "brainlink_settings_btn"):
            self.brainlink_settings_btn.show()
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
        self._create_brainlink_general_tab(font)
        
        # Close button — на 1/6 экрана ниже (aspect2d: ~0.17 вниз)
        self.settings_close_btn = DirectButton(
            text=t("settings.close"),
            text_scale=0.04,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.5, 0.2, 0.2, 1),
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            pos=(0, 0, -0.62),
            command=self._close_settings_panel,
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

    def _create_brainlink_settings_panel(self, font):
        """Separate BrainLink settings screen (not a tab in general settings)."""
        self.brainlink_settings_frame = DirectFrame(
            frameColor=(0.05, 0.05, 0.1, 0.9),
            frameSize=(-0.62, 0.62, -0.62, 0.52),
            pos=(0, 0, 0.0),
            borderWidth=(0.008, 0.008),
            borderUvWidth=(0.008, 0.008),
        )
        self.brainlink_settings_title = DirectLabel(
            text=t("settings.brainlink_title"),
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.44),
            parent=self.brainlink_settings_frame,
            text_font=font,
            text_align=TextNode.ACenter,
        )
        # Close first so tab content draws above it (DirectGui paint order).
        self.brainlink_settings_close_btn = DirectButton(
            text=t("settings.close"),
            text_scale=0.035,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.5, 0.2, 0.2, 1),
            frameSize=(-0.28, 0.28, -0.045, 0.045),
            pos=(0, 0, -0.565),
            command=self._close_brainlink_settings_panel,
            parent=self.brainlink_settings_frame,
            text_font=font,
            relief=1,
            borderWidth=(0.005, 0.005),
        )
        self._create_brainlink_tab(font)
        if font:
            self._apply_font_to_button(self.brainlink_settings_close_btn, font)
        self.brainlink_settings_frame.hide()
    
    def _create_settings_tabs(self, font):
        """Create tab buttons for settings categories"""
        self.settings_tabs = {}
        self.current_tab = "resolution"
        
        # Tab button width is 0.36 (from -0.18 to 0.18), so spacing them with gaps
        tab_positions = [
            (t("settings.tab_resolution"), "resolution", -0.38),
            (t("settings.tab_controls"), "controls", 0.0),
            (t("settings.tab_brainlink"), "brainlink", 0.38),
        ]
        
        self._tab_label_keys = {
            "resolution": "settings.tab_resolution",
            "controls": "settings.tab_controls",
            "brainlink": "settings.tab_brainlink",
        }
        
        for text, tab_id, x_pos in tab_positions:
            btn = DirectButton(
                text=text,
                text_scale=0.028,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.2, 0.2, 0.3, 1),
                frameSize=(-0.15, 0.15, -0.05, 0.05),
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
            frameSize=(-0.55, 0.55, -0.58, 0.32),
            pos=(0, 0, 0.02),
            parent=self.settings_frame
        )
        
        cheater_mode = False
        if hasattr(self.base, 'game_config'):
            cheater_mode = self.base.game_config.get("player", {}).get("cheater_mode", False)
        
        self.cheater_mode_label = DirectLabel(
            text=t("settings.cheater_mode"),
            text_scale=0.034,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.45, 0, 0.26),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        self.cheater_mode_hint = DirectLabel(
            text=t("settings.cheater_hint"),
            text_scale=0.026,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.45, 0, 0.20),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ALeft
        )
        self.cheater_mode_checkbox = DirectButton(
            text="+" if cheater_mode else "",
            text_scale=0.05,
            text_fg=(0.9, 1, 0.9, 1) if cheater_mode else (0.5, 0.5, 0.5, 1),
            frameColor=(0.15, 0.4, 0.2, 1) if cheater_mode else (0.22, 0.22, 0.28, 1),
            frameSize=(-0.055, 0.055, -0.045, 0.045),
            pos=(0.42, 0, 0.23),
            command=self._toggle_cheater_mode,
            parent=self.controls_frame,
            text_font=font,
            relief=2,
            borderWidth=(0.008, 0.008),
        )
        
        DirectLabel(
            text=t("settings.keys_col_brainlink"),
            text_scale=0.026,
            text_fg=(0.75, 0.85, 1.0, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0.12, 0, 0.11),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ACenter,
        )
        DirectLabel(
            text=t("settings.keys_col_local"),
            text_scale=0.026,
            text_fg=(0.75, 1.0, 0.85, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0.42, 0, 0.11),
            parent=self.controls_frame,
            text_font=font,
            text_align=TextNode.ACenter,
        )

        default_keys = {"up": "arrow_up", "down": "arrow_down", "left": "arrow_left", "right": "arrow_right", "action": "space", "sit_pause": "p"}
        default_local = {a: "" for a in default_keys}
        controls_root = self.base.game_config.get("controls", {}) if hasattr(self.base, "game_config") else {}
        controls_cfg = controls_root.get("keyboard", default_keys)
        controls_local_cfg = controls_root.get("keyboard_local", default_local)
        key_labels = [
            ("settings.key_up", "up"),
            ("settings.key_down", "down"),
            ("settings.key_left", "left"),
            ("settings.key_right", "right"),
            ("settings.key_sit", "action"),
            ("settings.key_sit_pause", "sit_pause"),
        ]
        self.controls_key_buttons = {}
        self.controls_key_buttons_local = {}
        self.controls_action_labels = {}
        row_step = 0.062
        keys_top_z = 0.04
        for i, (label_key, action) in enumerate(key_labels):
            z = keys_top_z - i * row_step
            lbl = DirectLabel(
                text=t(label_key) + ":",
                text_scale=0.028,
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
                text_scale=0.026,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.25, 0.25, 0.4, 1),
                frameSize=(-0.14, 0.14, -0.032, 0.032),
                pos=(0.12, 0, z),
                command=self._start_rebind_key,
                extraArgs=[action, "keyboard"],
                parent=self.controls_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.004, 0.004)
            )
            self.controls_key_buttons[action] = btn
            local_key = controls_local_cfg.get(action, "")
            btn_local = DirectButton(
                text=self._key_display_name(local_key),
                text_scale=0.026,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.2, 0.35, 0.3, 1),
                frameSize=(-0.14, 0.14, -0.032, 0.032),
                pos=(0.42, 0, z),
                command=self._start_rebind_key,
                extraArgs=[action, "keyboard_local"],
                parent=self.controls_frame,
                text_font=font,
                relief=1,
                borderWidth=(0.004, 0.004)
            )
            self.controls_key_buttons_local[action] = btn_local
        
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
        self._rebind_column = "keyboard"
        self.REBIND_KEYS = [
            "arrow_up", "arrow_down", "arrow_left", "arrow_right",
            "space", "w", "a", "s", "d", "p", "r", "t", "f", "g", "e", "q", "z", "x", "c", "v", "b", "n", "m",
            "return", "backspace", "tab", "shift", "control", "alt",
            "numpad2", "numpad4", "numpad6", "numpad8",
        ]
    
    def _key_display_name(self, key_name: str) -> str:
        """Human-readable key name for display."""
        if not key_name:
            return t("settings.key_unbound")
        s = key_name.replace("arrow_", "").replace("-", " ").strip()
        return s[:1].upper() + s[1:] if s else key_name
    
    def _start_rebind_key(self, action: str, column: str = "keyboard"):
        """Start listening for next key press to rebind."""
        if self._rebind_action:
            return
        self._rebind_action = action
        self._rebind_column = column
        btn = self.controls_key_buttons.get(action) if column == "keyboard" else self.controls_key_buttons_local.get(action)
        if btn:
            btn["text"] = t("settings.rebind_wait")
        for key in self.REBIND_KEYS:
            self.base.accept(key, self._on_rebind_key, [key])
    
    def _on_rebind_key(self, key_name: str):
        """Assign key to current action and stop listening."""
        if not self._rebind_action:
            return
        action = self._rebind_action
        column = self._rebind_column or "keyboard"
        self._rebind_action = None
        self._rebind_column = "keyboard"
        for key in self.REBIND_KEYS:
            self.base.ignore(key)
        
        if not hasattr(self.base, "game_config"):
            return
        if key_name == "backspace":
            key_name = ""
        ctrl = self.base.game_config.get("controls", {})
        kbd = ctrl.get(column, {})
        kbd[action] = key_name
        ctrl[column] = kbd
        self.base.game_config["controls"] = ctrl
        
        try:
            config_path = Path("config/game_config.json")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                controls = config.setdefault("controls", {})
                controls[column] = kbd
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save key config: %s", e)
        
        if hasattr(self.base, "input_manager") and self.base.input_manager:
            self.base.input_manager.rebind_keys()
        
        btn = self.controls_key_buttons.get(action) if column == "keyboard" else self.controls_key_buttons_local.get(action)
        if btn:
            btn["text"] = self._key_display_name(key_name)
        logger.info("Key bound (%s): %s -> %s", column, action, key_name or "(none)")
    
    def _create_brainlink_general_tab(self, font):
        """General BrainLink params (thresholds, weights) under Settings → BrainLink tab."""
        self.brainlink_general_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.55, 0.55, -0.42, 0.28),
            pos=(0, 0, 0.05),
            parent=self.settings_frame,
        )
        bl_config = {}
        if hasattr(self.base, "game_config"):
            bl_config = self.base.game_config.get("brainlink", {})
        self._build_brainlink_general_params_ui(self.brainlink_general_frame, font, bl_config)
        self.brainlink_general_frame.hide()

    def _build_brainlink_general_params_ui(self, parent, font, bl_config):
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

        if not hasattr(self, "brainlink_field_labels"):
            self.brainlink_field_labels = {}

        def _config_entry_row(label_key, z_pos, config_key, default_val, width=5):
            val = bl_config.get(config_key, default_val)
            text = _float_fmt(val)
            lbl = DirectLabel(
                text=t(label_key),
                text_scale=0.028,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(-0.5, 0, z_pos),
                parent=parent,
                text_font=font,
                text_align=TextNode.ALeft,
            )
            self.brainlink_field_labels[config_key] = (lbl, label_key)
            entry = DirectEntry(
                parent=parent,
                scale=0.032,
                pos=(0.38, 0, z_pos),
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

        _row = 0.18
        _step = 0.055
        self.brainlink_entries = {
            "confidence_threshold": {
                "entry": _config_entry_row("settings.bl_conf_threshold", _row, "confidence_threshold", 0.5),
                "default": 0.5,
                "parse": _float_parse,
                "fmt": _float_fmt,
                "clamp": (0.0, 1.0),
            },
            "min_confidence": {
                "entry": _config_entry_row("settings.bl_min_confidence", _row - _step, "min_confidence", 0.25),
                "default": 0.25,
                "parse": _float_parse,
                "fmt": _float_fmt,
                "clamp": (0.0, 1.0),
            },
            "full_confidence": {
                "entry": _config_entry_row("settings.bl_full_confidence", _row - 2 * _step, "full_confidence", 0.7),
                "default": 0.7,
                "parse": _float_parse,
                "fmt": _float_fmt,
                "clamp": (0.0, 1.0),
            },
        }

        weights = bl_config.get("prediction_weights", [1.0, 1.0, 1.0, 1.0])
        weights_str = ", ".join(str(round(w, 2)) for w in (weights + [1.0] * 4)[:4])
        _weights_z = _row - 3 * _step
        self.brainlink_weights_label = DirectLabel(
            text=t("settings.bl_weights"),
            text_scale=0.028,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, _weights_z),
            parent=parent,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        self._brainlink_cached_weights = weights_str
        self.brainlink_weights_entry = DirectEntry(
            parent=parent,
            scale=0.032,
            pos=(0.05, 0, _weights_z),
            width=16,
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
        _apply_z = _weights_z - _step
        self.brainlink_apply_btn = DirectButton(
            text=t("settings.apply"),
            text_scale=0.028,
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.1, 0.1, -0.03, 0.03),
            pos=(0.38, 0, _apply_z),
            command=self._brainlink_apply_ml_config,
            parent=parent,
            text_font=font,
        )

    def _brainlink_populate_fault_grid(
        self,
        parent,
        font,
        entry_font,
        entry_color,
        values: dict,
        defaults: dict,
        entries_out: dict,
        labels_out: dict,
        cached_out: dict,
        fault_label_keys: dict,
        label_suffix: str,
        top_z: float,
        row_step: float = 0.044,
        rows_per_col: int = 6,
        entry_scale: float = 0.028,
    ) -> float:
        """Two-column fault grid (6+5 rows); returns lowest z used."""
        lowest = top_z
        for idx, field in enumerate(BRAINLINK_BASE_FAULT_FIELDS):
            col = 0 if idx < rows_per_col else 1
            row = idx if col == 0 else idx - rows_per_col
            if col == 0:
                x_lbl, x_entry = -0.50, -0.24
            else:
                x_lbl, x_entry = 0.02, 0.28
            z_pos = top_z - row * row_step
            lowest = min(lowest, z_pos)
            lbl_key = fault_label_keys[field]
            lbl = DirectLabel(
                text=t(lbl_key) + label_suffix,
                text_scale=0.023,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(x_lbl, 0, z_pos),
                parent=parent,
                text_font=font,
                text_align=TextNode.ALeft,
            )
            labels_out[field] = (lbl, lbl_key)
            val = int(values.get(field, defaults[field]))
            text = str(val)
            entry = DirectEntry(
                parent=parent,
                scale=entry_scale,
                pos=(x_entry, 0, z_pos),
                width=4,
                numLines=1,
                initialText=text,
                entryFont=entry_font,
                frameColor=entry_color,
                borderWidth=(0.006, 0.006),
                focus=0,
            )
            entry.enterText(text)
            entries_out[field] = entry
            cached_out[field] = text
        return lowest

    def _create_brainlink_tab(self, font):
        """Create BrainLink settings content (standalone panel)."""
        self.brainlink_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.58, 0.58, -0.52, 0.38),
            pos=(0, 0, 0.0),
            parent=self.brainlink_settings_frame
        )

        bl_config = {}
        if hasattr(self.base, "game_config"):
            bl_config = self.base.game_config.get("brainlink", {})
        prediction_mode = bl_config.get("prediction_mode", "base")
        if prediction_mode not in ("base", "ml"):
            prediction_mode = "base"

        entry_font = DGG.getDefaultFont()
        _entry_color = (0.28, 0.32, 0.45, 1)
        _chk_size = (-0.04, 0.04, -0.03, 0.03)
        z_mode = 0.34
        z_chk = (0.28, 0.23, 0.18)
        z_content = 0.11

        self.brainlink_mode_label = DirectLabel(
            text=t("settings.bl_prediction_mode"),
            text_scale=0.03,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, z_mode),
            parent=self.brainlink_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        active_mode = (0.3, 0.5, 0.35, 1)
        idle_mode = (0.25, 0.25, 0.35, 1)
        self.brainlink_mode_base_btn = DirectButton(
            text=t("settings.bl_mode_base"),
            text_scale=0.026,
            frameColor=active_mode if prediction_mode == "base" else idle_mode,
            frameSize=(-0.09, 0.09, -0.03, 0.03),
            pos=(-0.08, 0, z_mode),
            command=self._brainlink_set_mode,
            extraArgs=["base"],
            parent=self.brainlink_frame,
            text_font=font,
        )
        self.brainlink_mode_ml_btn = DirectButton(
            text=t("settings.bl_mode_ml"),
            text_scale=0.026,
            frameColor=active_mode if prediction_mode == "ml" else idle_mode,
            frameSize=(-0.09, 0.09, -0.03, 0.03),
            pos=(0.12, 0, z_mode),
            command=self._brainlink_set_mode,
            extraArgs=["ml"],
            parent=self.brainlink_frame,
            text_font=font,
        )

        settings = [
            ("settings.bl_send_keyboard", "send_keyboard_events", z_chk[0], bl_config.get("send_keyboard_events", True)),
            ("settings.bl_send_history", "send_to_history", z_chk[1], bl_config.get("send_to_history", True)),
            ("settings.bl_send_ml", "send_to_ml", z_chk[1], bl_config.get("send_to_ml", True)),
            ("settings.bl_send_events", "send_brainlink_events", z_chk[2], bl_config.get("send_brainlink_events", True)),
        ]
        self.brainlink_checkboxes = {}
        self.brainlink_setting_labels = {}
        for label_key, key, z_pos, default_value in settings:
            lbl = DirectLabel(
                text=t(label_key) + ":",
                text_scale=0.026,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                pos=(-0.5, 0, z_pos),
                parent=self.brainlink_frame,
                text_font=font,
                text_align=TextNode.ALeft,
            )
            self.brainlink_setting_labels[key] = (lbl, label_key)
            checkbox = DirectButton(
                text="+" if default_value else "",
                text_scale=0.04,
                text_fg=(0.9, 1, 0.9, 1) if default_value else (0.5, 0.5, 0.5, 1),
                frameColor=(0.15, 0.4, 0.2, 1) if default_value else (0.22, 0.22, 0.28, 1),
                frameSize=_chk_size,
                pos=(0.38, 0, z_pos),
                command=self._toggle_brainlink_setting,
                extraArgs=[key],
                parent=self.brainlink_frame,
                text_font=font,
                relief=2,
                borderWidth=(0.008, 0.008),
            )
            self.brainlink_checkboxes[key] = checkbox

        self.brainlink_base_panel = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.58, 0.58, -0.55, 0.02),
            pos=(0, 0, z_content),
            parent=self.brainlink_frame,
        )
        self.brainlink_base_fault_title = DirectLabel(
            text=t("settings.bl_base_fault_title"),
            text_scale=0.026,
            text_fg=(0.85, 0.9, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.50, 0, 0.02),
            parent=self.brainlink_base_panel,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        base_fault = dict(DEFAULT_BASE_FAULT)
        base_fault.update(bl_config.get("base_fault") or {})
        self.brainlink_fault_entries = {}
        self.brainlink_fault_labels = {}
        self._brainlink_cached_fault = {}
        fault_label_keys = {f: f"settings.bl_fault_{f}" for f in BRAINLINK_BASE_FAULT_FIELDS}
        _base_bottom = self._brainlink_populate_fault_grid(
            self.brainlink_base_panel,
            font,
            entry_font,
            _entry_color,
            base_fault,
            DEFAULT_BASE_FAULT,
            self.brainlink_fault_entries,
            self.brainlink_fault_labels,
            self._brainlink_cached_fault,
            fault_label_keys,
            "",
            top_z=-0.03,
        )

        multi_fault = dict(DEFAULT_MULTI_FAULT)
        multi_fault.update(bl_config.get("multi_fault") or {})
        multi_count = int(bl_config.get("multi_count", DEFAULT_MULTI_COUNT) or DEFAULT_MULTI_COUNT)
        _multi_title_z = _base_bottom - 0.048
        self.brainlink_multi_fault_title = DirectLabel(
            text=t("settings.bl_multi_fault_title"),
            text_scale=0.024,
            text_fg=(0.85, 0.9, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.50, 0, _multi_title_z),
            parent=self.brainlink_base_panel,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        self.brainlink_multi_fault_entries = {}
        self.brainlink_multi_fault_labels = {}
        self._brainlink_cached_multi_fault = {}
        _multi_bottom = self._brainlink_populate_fault_grid(
            self.brainlink_base_panel,
            font,
            entry_font,
            _entry_color,
            multi_fault,
            DEFAULT_MULTI_FAULT,
            self.brainlink_multi_fault_entries,
            self.brainlink_multi_fault_labels,
            self._brainlink_cached_multi_fault,
            fault_label_keys,
            " ×",
            top_z=_multi_title_z - 0.04,
        )

        _multi_count_z = _multi_bottom - 0.044
        self.brainlink_multi_count_label = DirectLabel(
            text=t("settings.bl_multi_count"),
            text_scale=0.022,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.50, 0, _multi_count_z),
            parent=self.brainlink_base_panel,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        self.brainlink_multi_count_entry = DirectEntry(
            parent=self.brainlink_base_panel,
            scale=0.028,
            pos=(-0.24, 0, _multi_count_z),
            width=4,
            numLines=1,
            initialText=str(max(1, multi_count)),
            entryFont=entry_font,
            frameColor=_entry_color,
            borderWidth=(0.005, 0.005),
            focus=0,
        )
        self.brainlink_multi_count_entry.enterText(str(max(1, multi_count)))
        self._brainlink_cached_multi_count = str(max(1, multi_count))

        self.brainlink_apply_fault_btn = DirectButton(
            text=t("settings.bl_apply_base_fault"),
            text_scale=0.022,
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=(-0.22, 0.22, -0.03, 0.03),
            pos=(0.0, 0, _multi_count_z - 0.058),
            command=self._brainlink_apply_base_fault,
            parent=self.brainlink_base_panel,
            text_font=font,
        )

        self.brainlink_ml_panel = DirectFrame(
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.58, 0.58, -0.52, 0.02),
            pos=(0, 0, z_content),
            parent=self.brainlink_frame,
        )

        model_path = bl_config.get("model_path") or "—"
        history_path = bl_config.get("history_path") or "—"
        _ml_path_z = 0.02
        self.brainlink_model_path_label = DirectLabel(
            text=t("settings.bl_model_path") + " " + self._brainlink_short_path(model_path),
            text_scale=0.02,
            text_fg=(0.75, 0.8, 0.9, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, _ml_path_z),
            parent=self.brainlink_ml_panel,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        self.brainlink_history_path_label = DirectLabel(
            text=t("settings.bl_history_path") + " " + self._brainlink_short_path(history_path),
            text_scale=0.02,
            text_fg=(0.75, 0.8, 0.9, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, _ml_path_z - 0.038),
            parent=self.brainlink_ml_panel,
            text_font=font,
            text_align=TextNode.ALeft,
        )

        _ml_btn_z1 = _ml_path_z - 0.09
        _ml_btn_z2 = _ml_btn_z1 - 0.055
        _ml_btn_w = 0.2
        _ml_btn_h = 0.028
        _ml_btn_frame = (-_ml_btn_w, _ml_btn_w, -_ml_btn_h, _ml_btn_h)
        self.brainlink_load_model_btn = DirectButton(
            text=t("settings.load_model"),
            text_scale=0.022,
            frameColor=(0.25, 0.25, 0.4, 1),
            frameSize=_ml_btn_frame,
            pos=(-0.26, 0, _ml_btn_z1),
            command=self._brainlink_load_model,
            parent=self.brainlink_ml_panel,
            text_font=font,
        )
        self.brainlink_save_model_btn = DirectButton(
            text=t("settings.save_model"),
            text_scale=0.022,
            frameColor=(0.25, 0.4, 0.25, 1),
            frameSize=_ml_btn_frame,
            pos=(0.26, 0, _ml_btn_z1),
            command=self._brainlink_save_model,
            parent=self.brainlink_ml_panel,
            text_font=font,
        )
        self.brainlink_reset_model_btn = DirectButton(
            text=t("settings.reset_model"),
            text_scale=0.022,
            frameColor=(0.45, 0.25, 0.25, 1),
            frameSize=_ml_btn_frame,
            pos=(-0.26, 0, _ml_btn_z2),
            command=self._brainlink_reset_model,
            parent=self.brainlink_ml_panel,
            text_font=font,
        )
        self.brainlink_load_history_btn = DirectButton(
            text=t("settings.load_history"),
            text_scale=0.022,
            frameColor=(0.25, 0.25, 0.4, 1),
            frameSize=_ml_btn_frame,
            pos=(0.26, 0, _ml_btn_z2),
            command=self._brainlink_load_history,
            parent=self.brainlink_ml_panel,
            text_font=font,
        )

        self.brainlink_command_status = DirectLabel(
            text="",
            text_scale=0.022,
            text_fg=(0.7, 0.85, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(-0.5, 0, -0.50),
            parent=self.brainlink_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )

        self._brainlink_prediction_mode = prediction_mode
        self._update_brainlink_mode_ui()
        self._brainlink_layout_close_button()

    def _brainlink_layout_close_button(self):
        """Keep Close button just below the active settings block; trim panel height."""
        close = getattr(self, "brainlink_settings_close_btn", None)
        if not close:
            return
        frame = getattr(self, "brainlink_frame", None)
        mode = getattr(self, "_brainlink_prediction_mode", "base")
        content_bottom = -0.48
        if frame:
            if mode == "base":
                panel = getattr(self, "brainlink_base_panel", None)
                apply_btn = getattr(self, "brainlink_apply_fault_btn", None)
                if panel and apply_btn:
                    content_bottom = (
                        frame.getZ()
                        + panel.getZ()
                        + apply_btn.getZ()
                        - 0.034
                    )
            elif hasattr(self, "brainlink_ml_panel"):
                ml = self.brainlink_ml_panel
                content_bottom = frame.getZ() + ml.getZ() - 0.14
        close_gap = 0.042
        close_half = 0.045
        close_z = content_bottom - close_gap - close_half
        close.setPos(0, 0, close_z)
        settings_frame = getattr(self, "brainlink_settings_frame", None)
        if settings_frame is not None:
            settings_frame["frameSize"] = (-0.62, 0.62, close_z - close_half - 0.02, 0.52)

    def _brainlink_short_path(self, path: str, max_len: int = 42) -> str:
        if not path or path == "—":
            return "—"
        s = str(path)
        return s if len(s) <= max_len else "…" + s[-(max_len - 1):]

    def _brainlink_ensure_client_config_path(self):
        config_path = Path("config/game_config.json").resolve()
        brainlink_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "BrainLink"
        brainlink_dir.mkdir(parents=True, exist_ok=True)
        (brainlink_dir / "game_config_path.txt").write_text(str(config_path), encoding="utf-8")

    def _brainlink_set_status(self, message: str, ok: bool = True):
        if hasattr(self, "brainlink_command_status"):
            self.brainlink_command_status["text"] = message
            self.brainlink_command_status["text_fg"] = (0.7, 0.9, 0.7, 1) if ok else (1, 0.6, 0.6, 1)

    def _brainlink_get_client(self):
        if not hasattr(self.base, "input_manager") or not self.base.input_manager:
            return None
        return getattr(self.base.input_manager, "brainlink", None)

    def _brainlink_send_client_command(self, method_name: str) -> bool:
        client = self._brainlink_get_client()
        if not client or not client.is_connected():
            self._brainlink_set_status(t("settings.bl_not_connected"), ok=False)
            logger.warning(t("settings.bl_not_connected"))
            return False
        self._save_brainlink_config()
        self._brainlink_ensure_client_config_path()
        time.sleep(0.15)
        send_fn = getattr(client, method_name, None)
        if not send_fn:
            self._brainlink_set_status(t("settings.bl_command_failed"), ok=False)
            return False
        if send_fn():
            self._brainlink_set_status(t("settings.bl_command_sent"), ok=True)
            return True
        self._brainlink_set_status(t("settings.bl_command_failed"), ok=False)
        return False

    def _brainlink_set_mode(self, mode: str):
        if mode not in ("base", "ml"):
            return
        if not hasattr(self.base, "game_config"):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        bl_config["prediction_mode"] = mode
        self.base.game_config["brainlink"] = bl_config
        self._brainlink_prediction_mode = mode
        self._update_brainlink_mode_ui()
        self._brainlink_send_client_command("send_set_prediction_mode_command")

    def _update_brainlink_mode_ui(self):
        mode = getattr(self, "_brainlink_prediction_mode", "base")
        active = (0.3, 0.5, 0.35, 1)
        idle = (0.25, 0.25, 0.35, 1)
        if hasattr(self, "brainlink_mode_base_btn"):
            self.brainlink_mode_base_btn["frameColor"] = active if mode == "base" else idle
        if hasattr(self, "brainlink_mode_ml_btn"):
            self.brainlink_mode_ml_btn["frameColor"] = active if mode == "ml" else idle
        if hasattr(self, "brainlink_base_panel"):
            if mode == "base":
                self.brainlink_base_panel.show()
            else:
                self.brainlink_base_panel.hide()
        if hasattr(self, "brainlink_ml_panel"):
            if mode == "ml":
                self.brainlink_ml_panel.show()
            else:
                self.brainlink_ml_panel.hide()
        for key in ("send_to_history",):
            for widget_key in (key,):
                lbl = self.brainlink_setting_labels.get(widget_key)
                cb = self.brainlink_checkboxes.get(widget_key)
                show = mode == "base"
                if lbl:
                    lbl[0].show() if show else lbl[0].hide()
                if cb:
                    cb.show() if show else cb.hide()
        for key in ("send_to_ml",):
            lbl = self.brainlink_setting_labels.get(key)
            cb = self.brainlink_checkboxes.get(key)
            show = mode == "ml"
            if lbl:
                lbl[0].show() if show else lbl[0].hide()
            if cb:
                cb.show() if show else cb.hide()
        self._brainlink_layout_close_button()

    def _brainlink_collect_fault_from_entries(
        self,
        entries: dict,
        defaults: dict,
        cached: dict,
    ) -> dict:
        fault = dict(defaults)
        for field, entry in entries.items():
            text = entry.get(plain=True).strip()
            try:
                fault[field] = int(text)
                entry.enterText(str(fault[field]))
                cached[field] = str(fault[field])
            except (ValueError, TypeError):
                fallback = fault.get(field, defaults[field])
                entry.enterText(str(fallback))
                fault[field] = int(fallback)
                cached[field] = str(fallback)
        return fault

    def _brainlink_collect_base_fault_from_ui(self) -> dict:
        bl_config = self.base.game_config.get("brainlink", {}) if hasattr(self.base, "game_config") else {}
        fault = dict(DEFAULT_BASE_FAULT)
        fault.update(bl_config.get("base_fault") or {})
        cached = getattr(self, "_brainlink_cached_fault", {})
        return self._brainlink_collect_fault_from_entries(
            getattr(self, "brainlink_fault_entries", {}),
            {**DEFAULT_BASE_FAULT, **fault},
            cached,
        )

    def _brainlink_collect_multi_fault_from_ui(self) -> dict:
        bl_config = self.base.game_config.get("brainlink", {}) if hasattr(self.base, "game_config") else {}
        fault = dict(DEFAULT_MULTI_FAULT)
        fault.update(bl_config.get("multi_fault") or {})
        cached = getattr(self, "_brainlink_cached_multi_fault", {})
        return self._brainlink_collect_fault_from_entries(
            getattr(self, "brainlink_multi_fault_entries", {}),
            {**DEFAULT_MULTI_FAULT, **fault},
            cached,
        )

    def _brainlink_collect_multi_count_from_ui(self) -> int:
        entry = getattr(self, "brainlink_multi_count_entry", None)
        fallback = DEFAULT_MULTI_COUNT
        if hasattr(self.base, "game_config"):
            fallback = int(
                self.base.game_config.get("brainlink", {}).get("multi_count", DEFAULT_MULTI_COUNT)
                or DEFAULT_MULTI_COUNT
            )
        if not entry:
            return max(1, fallback)
        text = entry.get(plain=True).strip()
        try:
            val = max(1, int(text))
            entry.enterText(str(val))
            self._brainlink_cached_multi_count = str(val)
            return val
        except (ValueError, TypeError):
            val = max(1, fallback)
            entry.enterText(str(val))
            self._brainlink_cached_multi_count = str(val)
            return val

    def _brainlink_apply_base_fault(self):
        if not hasattr(self.base, "game_config"):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        bl_config["base_fault"] = self._brainlink_collect_base_fault_from_ui()
        bl_config["multi_fault"] = self._brainlink_collect_multi_fault_from_ui()
        bl_config["multi_count"] = self._brainlink_collect_multi_count_from_ui()
        self.base.game_config["brainlink"] = bl_config
        self._save_brainlink_config()
        self._brainlink_send_client_command("send_apply_base_fault_command")

    def _brainlink_refresh_path_labels(self):
        bl_config = getattr(self.base, "game_config", {}).get("brainlink", {})
        if hasattr(self, "brainlink_model_path_label"):
            mp = bl_config.get("model_path") or "—"
            self.brainlink_model_path_label["text"] = t("settings.bl_model_path") + " " + self._brainlink_short_path(mp)
        if hasattr(self, "brainlink_history_path_label"):
            hp = bl_config.get("history_path") or "—"
            self.brainlink_history_path_label["text"] = t("settings.bl_history_path") + " " + self._brainlink_short_path(hp)

    def _brainlink_reset_model(self):
        self._brainlink_send_client_command("send_reset_model_command")

    def _brainlink_load_history(self):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title=t("settings.load_history"),
            filetypes=[("JSON history", "*.json"), ("All files", "*.*")],
        )
        root.destroy()
        if not path or not hasattr(self.base, "game_config"):
            return
        path_abs = str(Path(path).resolve())
        bl_config = self.base.game_config.get("brainlink", {})
        bl_config["history_path"] = path_abs
        self.base.game_config["brainlink"] = bl_config
        self._brainlink_refresh_path_labels()
        self._brainlink_send_client_command("send_load_history_command")
    
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

    def _refresh_brainlink_fault_ui_from_config(self):
        """Reload Base / Multi fault fields and multi_count from game config."""
        if not hasattr(self.base, "game_config"):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        base_fault = dict(DEFAULT_BASE_FAULT)
        base_fault.update(bl_config.get("base_fault") or {})
        for field, entry in getattr(self, "brainlink_fault_entries", {}).items():
            val = int(base_fault.get(field, DEFAULT_BASE_FAULT[field]))
            text = str(val)
            entry.enterText(text)
            if hasattr(self, "_brainlink_cached_fault"):
                self._brainlink_cached_fault[field] = text
        multi_fault = dict(DEFAULT_MULTI_FAULT)
        multi_fault.update(bl_config.get("multi_fault") or {})
        for field, entry in getattr(self, "brainlink_multi_fault_entries", {}).items():
            val = int(multi_fault.get(field, DEFAULT_MULTI_FAULT[field]))
            text = str(val)
            entry.enterText(text)
            if hasattr(self, "_brainlink_cached_multi_fault"):
                self._brainlink_cached_multi_fault[field] = text
        multi_count = max(1, int(bl_config.get("multi_count", DEFAULT_MULTI_COUNT) or DEFAULT_MULTI_COUNT))
        if hasattr(self, "brainlink_multi_count_entry"):
            self.brainlink_multi_count_entry.enterText(str(multi_count))
            self._brainlink_cached_multi_count = str(multi_count)

    def _refresh_brainlink_entries_from_config(self):
        """Reload BrainLink input fields from current game config."""
        if not hasattr(self.base, "game_config"):
            return
        bl_config = self.base.game_config.get("brainlink", {})
        if hasattr(self, "brainlink_entries"):
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
            mode = bl_config.get("prediction_mode", "base")
            if mode not in ("base", "ml"):
                mode = "base"
            self._brainlink_prediction_mode = mode
        self._refresh_brainlink_fault_ui_from_config()
        self._brainlink_refresh_path_labels()

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
        """Choose model file, save path to config, command client to load."""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title=t("settings.load_model"),
            filetypes=[("Model files", "*.pkl *.joblib *.pt *.onnx"), ("All files", "*.*")],
        )
        root.destroy()
        if not path or not hasattr(self.base, "game_config"):
            return
        path_abs = str(Path(path).resolve())
        bl_config = self.base.game_config.get("brainlink", {})
        bl_config["model_path"] = path_abs
        self.base.game_config["brainlink"] = bl_config
        self._brainlink_refresh_path_labels()
        self._brainlink_send_client_command("send_load_model_command")
        logger.info("BrainLink model path set (load): %s", path_abs)

    def _brainlink_save_model(self):
        """Choose save path, write config, command client to save model."""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            title=t("settings.save_model"),
            defaultextension=".pkl",
            filetypes=[("Pickle model", "*.pkl"), ("Model files", "*.pkl *.joblib *.pt *.onnx"), ("All files", "*.*")],
        )
        root.destroy()
        if not path or not hasattr(self.base, "game_config"):
            return
        path_abs = str(Path(path).resolve())
        bl_config = self.base.game_config.get("brainlink", {})
        bl_config["model_path"] = path_abs
        self.base.game_config["brainlink"] = bl_config
        self._brainlink_refresh_path_labels()
        self._brainlink_send_client_command("send_save_model_command")
        logger.info("BrainLink model path set (save): %s", path_abs)
    
    def _switch_settings_tab(self, tab_id: str):
        """Switch between settings tabs"""
        self.current_tab = tab_id
        
        # Hide all frames
        self.resolution_frame.hide()
        self.controls_frame.hide()
        if hasattr(self, "brainlink_general_frame"):
            self.brainlink_general_frame.hide()
        
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
            self.brainlink_general_frame.show()
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
    
    def _set_cheater_checkbox_visual(self, enabled: bool):
        cb = getattr(self, "cheater_mode_checkbox", None)
        if not cb:
            return
        cb["text"] = "+" if enabled else ""
        cb["text_fg"] = (0.9, 1, 0.9, 1) if enabled else (0.5, 0.5, 0.5, 1)
        cb["frameColor"] = (0.15, 0.4, 0.2, 1) if enabled else (0.22, 0.22, 0.28, 1)

    def _toggle_cheater_mode(self):
        """Toggle cheater mode (unlimited energy)"""
        if not hasattr(self.base, 'game_config'):
            return
        
        player_config = self.base.game_config.get("player", {})
        current_value = player_config.get("cheater_mode", False)
        new_value = not current_value
        
        player_config["cheater_mode"] = new_value
        self.base.game_config["player"] = player_config
        
        self._set_cheater_checkbox_visual(new_value)
        
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
        if hasattr(self, "brainlink_settings_btn"):
            self.brainlink_settings_btn["text"] = t("menu.brainlink_settings")
        self.quit_btn["text"] = t("menu.quit")
        self.back_to_game_btn["text"] = t("menu.back_to_game")
        self.controls_text.setText(t("menu.controls_hint"))
        self.settings_title["text"] = t("settings.title")
        self.settings_close_btn["text"] = t("settings.close")
        if hasattr(self, "brainlink_settings_title"):
            self.brainlink_settings_title["text"] = t("settings.brainlink_title")
        if hasattr(self, "brainlink_settings_close_btn"):
            self.brainlink_settings_close_btn["text"] = t("settings.close")
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
        if hasattr(self, "brainlink_reset_model_btn"):
            self.brainlink_reset_model_btn["text"] = t("settings.reset_model")
        if hasattr(self, "brainlink_load_history_btn"):
            self.brainlink_load_history_btn["text"] = t("settings.load_history")
        if hasattr(self, "brainlink_mode_label"):
            self.brainlink_mode_label["text"] = t("settings.bl_prediction_mode")
        if hasattr(self, "brainlink_mode_base_btn"):
            self.brainlink_mode_base_btn["text"] = t("settings.bl_mode_base")
        if hasattr(self, "brainlink_mode_ml_btn"):
            self.brainlink_mode_ml_btn["text"] = t("settings.bl_mode_ml")
        if hasattr(self, "brainlink_base_fault_title"):
            self.brainlink_base_fault_title["text"] = t("settings.bl_base_fault_title")
        if hasattr(self, "brainlink_multi_fault_title"):
            self.brainlink_multi_fault_title["text"] = t("settings.bl_multi_fault_title")
        if hasattr(self, "brainlink_multi_count_label"):
            self.brainlink_multi_count_label["text"] = t("settings.bl_multi_count")
        if hasattr(self, "brainlink_apply_fault_btn"):
            self.brainlink_apply_fault_btn["text"] = t("settings.bl_apply_base_fault")
        for field, (lbl, lbl_key) in getattr(self, "brainlink_fault_labels", {}).items():
            lbl["text"] = t(lbl_key)
        for field, (lbl, lbl_key) in getattr(self, "brainlink_multi_fault_labels", {}).items():
            lbl["text"] = t(lbl_key) + " ×"
        self._brainlink_refresh_path_labels()
        self._update_brainlink_mode_ui()
    
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
            tmp_path = config_path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            tmp_path.replace(config_path)
            logger.info(f"Saved game config to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save game config: {e}")

    def _on_settings_clicked(self):
        """Toggle general settings (resolution / controls)."""
        self._toggle_settings_panel()

    def _on_brainlink_settings_clicked(self):
        """Toggle standalone BrainLink settings screen."""
        self._toggle_brainlink_settings_panel()

    def _hide_main_menu_for_settings(self):
        self.play_btn.hide()
        self.back_to_game_btn.hide()
        self.settings_btn.hide()
        if hasattr(self, "brainlink_settings_btn"):
            self.brainlink_settings_btn.hide()
        self.quit_btn.hide()
        self.controls_text.hide()
        if hasattr(self, "player_name_label"):
            self.player_name_label.hide()
        if hasattr(self, "player_name_entry"):
            self.player_name_entry.hide()
        if hasattr(self, "status_frame"):
            self.status_frame.hide()
        self.title.hide()
        self.subtitle.hide()

    def _show_main_menu_after_settings(self):
        if getattr(self.base, "_from_pause_settings", False):
            if hasattr(self.base, "_return_from_settings_to_game"):
                self.base._return_from_settings_to_game()
            return
        self._update_from_pause_buttons()
        self.settings_btn.show()
        if hasattr(self, "brainlink_settings_btn"):
            self.brainlink_settings_btn.show()
        self.quit_btn.show()
        self.controls_text.show()
        if hasattr(self, "player_name_label"):
            self.player_name_label.show()
        if hasattr(self, "player_name_entry"):
            self.player_name_entry.show()
        if hasattr(self, "status_frame"):
            self.status_frame.show()
        self.title.show()
        self.subtitle.show()

    def _close_settings_panel(self):
        if hasattr(self, "brainlink_entries"):
            self._brainlink_apply_ml_config()
        self.settings_frame.hide()
        self._show_main_menu_after_settings()

    def _close_brainlink_settings_panel(self):
        self.brainlink_settings_frame.hide()
        self._show_main_menu_after_settings()

    def _open_settings_panel(self, tab_id: str = "resolution"):
        """Open general settings (resolution / controls)."""
        if hasattr(self, "brainlink_settings_frame") and not self.brainlink_settings_frame.isHidden():
            self.brainlink_settings_frame.hide()
        self.settings_frame.show()
        self._switch_settings_tab(tab_id)
        self._refresh_resolution_ui()
        self._hide_main_menu_for_settings()

    def _open_brainlink_settings_panel(self):
        """Open standalone BrainLink settings."""
        if not self.settings_frame.isHidden():
            self.settings_frame.hide()
        self.brainlink_settings_frame.show()
        sync_brainlink_config_from_client(self.base)
        self._refresh_brainlink_entries_from_config()
        self._update_brainlink_mode_ui()
        self._brainlink_refresh_path_labels()
        self._hide_main_menu_for_settings()

    def _toggle_settings_panel(self):
        if not self.settings_frame.isHidden():
            self._close_settings_panel()
            return
        self._open_settings_panel("resolution")

    def _toggle_brainlink_settings_panel(self):
        if not self.brainlink_settings_frame.isHidden():
            self._close_brainlink_settings_panel()
            return
        self._open_brainlink_settings_panel()

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
