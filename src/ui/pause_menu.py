"""Pause menu UI — открывается по ESC в игре"""

import logging
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode
from src.core.i18n import t

logger = logging.getLogger(__name__)


class PauseMenu:
    """Меню паузы: начать этап сначала, загрузка, настройки, выход"""

    def __init__(self, base):
        self.base = base
        self.is_visible = False
        self.frame = None
        self.buttons = []
        self._button_keys = []
        self.title_label = None
        self._create_ui()

    def _create_ui(self):
        font = None
        if hasattr(self.base, "cyrillic_font") and self.base.cyrillic_font:
            font = self.base.cyrillic_font

        self.frame = DirectFrame(
            frameColor=(0.05, 0.05, 0.12, 0.92),
            frameSize=(-0.45, 0.45, -0.55, 0.35),
            pos=(0, 0, 0),
            borderWidth=(0.008, 0.008),
        )
        self.frame.setBin("fixed", 100)

        self.title_label = DirectLabel(
            text=t("pause.title"),
            text_scale=0.08,
            text_fg=(1, 0.9, 0.4, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.28),
            parent=self.frame,
            text_font=font,
            text_align=TextNode.ACenter,
        )
        if font:
            self._apply_font_to_label(self.title_label, font)

        options = [
            ("pause.restart", "restart"),
            ("pause.load", "load"),
            ("pause.settings", "settings"),
            ("pause.exit", "exit"),
        ]
        btn_h = 0.07
        spacing = 0.08
        start_y = 0.12
        for i, (text_key, key) in enumerate(options):
            y = start_y - i * (btn_h + spacing)
            btn = DirectButton(
                text=t(text_key),
                text_scale=0.045,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.2, 0.25, 0.4, 1),
                frameSize=(-0.38, 0.38, -btn_h / 2, btn_h / 2),
                pos=(0, 0, y),
                command=self._on_option,
                extraArgs=[key],
                parent=self.frame,
                text_font=font,
            )
            if font:
                self._apply_font_to_button(btn, font)
            self.buttons.append(btn)
            self._button_keys.append(text_key)

        self.frame.reparentTo(self.base.aspect2d)
        self.frame.hide()

    def refresh_locale(self):
        if self.title_label:
            self.title_label["text"] = t("pause.title")
        for btn, text_key in zip(self.buttons, self._button_keys):
            btn["text"] = t(text_key)

    def _apply_font_to_label(self, label, font):
        try:
            label["text_font"] = font
            c = label.component("text")
            if c:
                c.setFont(font)
        except Exception:
            pass

    def _apply_font_to_button(self, button, font):
        try:
            button["text_font"] = font
            for i in range(4):
                c = button.component(f"text{i}")
                if c:
                    c.setFont(font)
        except Exception:
            pass

    def _on_option(self, key: str):
        if key == "restart" and hasattr(self.base, "on_pause_restart"):
            self.base.on_pause_restart()
        elif key == "load" and hasattr(self.base, "on_pause_load"):
            self.base.on_pause_load()
        elif key == "settings" and hasattr(self.base, "on_pause_settings"):
            self.base.on_pause_settings()
        elif key == "exit" and hasattr(self.base, "on_pause_exit"):
            self.base.on_pause_exit()

    def show(self):
        self.frame.show()
        self.is_visible = True
        logger.debug("Pause menu shown")

    def hide(self):
        self.frame.hide()
        self.is_visible = False
        logger.debug("Pause menu hidden")
