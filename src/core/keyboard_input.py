"""
Клавиатурный ввод — состояние клавиш и движение от клавиш.
"""

import logging
from typing import Optional, Callable, Tuple
from direct.showbase.DirectObject import DirectObject

logger = logging.getLogger(__name__)


class KeyboardInput(DirectObject):
    """
    Обработка ввода с клавиатуры: привязки клавиш, состояние, направление движения.
    Не знает о BrainLink — только клавиши и движение (x, y) + событие "ml"/"mr"/"mu"/"md".
    """

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "action": False,
            "sit_pause": False,
        }
        self.on_action: Optional[Callable] = None
        self.on_sit_pause: Optional[Callable] = None

        self._key_bindings: dict = {}
        self._bound_keys: list = []

        self._apply_key_bindings()
        logger.debug("KeyboardInput initialized")

    def _get_keyboard_config(self) -> dict:
        default = {
            "up": "arrow_up", "down": "arrow_down", "left": "arrow_left", "right": "arrow_right",
            "action": "space", "sit_pause": "p",
        }
        if hasattr(self.base, "game_config"):
            return self.base.game_config.get("controls", {}).get("keyboard", default)
        return default

    def _apply_key_bindings(self):
        for key_name, _ in self._bound_keys:
            self.ignore(key_name)
            self.ignore(key_name + "-up")
        self._bound_keys.clear()
        self.ignore("escape")

        self._key_bindings = self._get_keyboard_config()
        if "space" in self._key_bindings and "action" not in self._key_bindings:
            self._key_bindings["action"] = self._key_bindings.get("space", "space")

        for internal, key_name in self._key_bindings.items():
            if not key_name or internal == "space":
                continue
            self.accept(key_name, self._on_key, [internal, True])
            self.accept(key_name + "-up", self._on_key, [internal, False])
            self._bound_keys.append((key_name, internal))

        self.accept("escape", self._on_escape_key)
        logger.debug("Keyboard bindings applied: %s", self._key_bindings)

    def _on_escape_key(self):
        if hasattr(self.base, "_on_escape"):
            self.base._on_escape()

    def _on_key(self, internal: str, pressed: bool):
        self.keys[internal] = pressed
        if internal in ("up", "down", "left", "right") and pressed:
            self.keys["action"] = False
        if internal == "action" and pressed and self.on_action:
            self.on_action()
        if internal == "sit_pause" and pressed and self.on_sit_pause:
            self.on_sit_pause()

    def get_movement_and_event(self) -> Tuple[Tuple[float, float], str]:
        """
        Текущее направление и событие движения с клавиатуры.
        Returns:
            ((x, y), event): event — "ml"|"mr"|"mu"|"md"|""; (x,y) нормализовано при диагонали.
        """
        x, y = 0.0, 0.0
        event = ""
        if self.keys["left"]:
            x -= 1
            event = "ml"
        elif self.keys["right"]:
            x += 1
            event = "mr"
        elif self.keys["up"]:
            y += 1
            event = "mu"
        elif self.keys["down"]:
            y -= 1
            event = "md"

        if x != 0 and y != 0:
            length = (x * x + y * y) ** 0.5
            x /= length
            y /= length
        return ((x, y), event)

    def is_action_pressed(self) -> bool:
        return self.keys.get("action", False)

    def clear_state(self):
        for k in ("up", "down", "left", "right", "action", "sit_pause"):
            self.keys[k] = False

    def rebind_keys(self):
        self._apply_key_bindings()

    def cleanup(self):
        self.ignoreAll()
        logger.debug("KeyboardInput cleaned up")
