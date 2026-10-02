"""
Клавиатурный ввод — состояние клавиш и движение от клавиш.
"""

import logging
from typing import Optional, Callable, Tuple
from direct.showbase.DirectObject import DirectObject

logger = logging.getLogger(__name__)

_ACTIONS = ("up", "down", "left", "right", "action", "sit_pause")


class KeyboardInput(DirectObject):
    """
    Обработка ввода с клавиатуры: две раскладки на действие.
    - keyboard: те же команды в игре + события для BrainLink
    - keyboard_local: те же команды без отправки в BrainLink
    """

    def __init__(self, base):
        super().__init__()
        self.base = base
        self._empty_keys = {a: False for a in _ACTIONS}
        self.keys_recordable = dict(self._empty_keys)
        self.keys_local = dict(self._empty_keys)

        self.on_action: Optional[Callable] = None
        self.on_sit_pause: Optional[Callable] = None

        self._bound_keys: list = []

        self._apply_key_bindings()
        logger.debug("KeyboardInput initialized")

    def _default_recordable(self) -> dict:
        return {
            "up": "arrow_up", "down": "arrow_down", "left": "arrow_left", "right": "arrow_right",
            "action": "space", "sit_pause": "p",
        }

    def _default_local(self) -> dict:
        return {a: "" for a in _ACTIONS}

    def _get_bindings(self, section: str) -> dict:
        if hasattr(self.base, "game_config"):
            ctrl = self.base.game_config.get("controls", {})
            if section == "keyboard":
                return dict(ctrl.get("keyboard", self._default_recordable()))
            return dict(ctrl.get("keyboard_local", self._default_local()))
        if section == "keyboard":
            return self._default_recordable()
        return self._default_local()

    def _apply_key_bindings(self):
        for key_name, _ in self._bound_keys:
            self.ignore(key_name)
            self.ignore(key_name + "-up")
        self._bound_keys.clear()
        self.ignore("escape")

        recordable = self._get_bindings("keyboard")
        local = self._get_bindings("keyboard_local")
        if "space" in recordable and "action" not in recordable:
            recordable["action"] = recordable.get("space", "space")

        self._bind_set(recordable, recordable=True)
        self._bind_set(local, recordable=False)

        self.accept("escape", self._on_escape_key)
        logger.debug("Keyboard bindings applied: recordable=%s local=%s", recordable, local)

    def _bind_set(self, bindings: dict, recordable: bool):
        for internal, key_name in bindings.items():
            if not key_name or internal == "space":
                continue
            if recordable:
                self.accept(key_name, self._on_key_recordable, [internal, True])
                self.accept(key_name + "-up", self._on_key_recordable, [internal, False])
            else:
                self.accept(key_name, self._on_key_local, [internal, True])
                self.accept(key_name + "-up", self._on_key_local, [internal, False])
            self._bound_keys.append((key_name, internal))

    def _on_escape_key(self):
        if hasattr(self.base, "_on_escape"):
            self.base._on_escape()

    def _on_key_recordable(self, internal: str, pressed: bool):
        self._apply_key_state(self.keys_recordable, internal, pressed)

    def _on_key_local(self, internal: str, pressed: bool):
        self._apply_key_state(self.keys_local, internal, pressed)

    def _apply_key_state(self, store: dict, internal: str, pressed: bool):
        store[internal] = pressed
        if internal in ("up", "down", "left", "right") and pressed:
            self.keys_recordable["action"] = False
            self.keys_local["action"] = False
        if internal == "action" and pressed and self.on_action:
            self.on_action()
        if internal == "sit_pause" and pressed and self.on_sit_pause:
            self.on_sit_pause()

    def _movement_from_keys(self, recordable: dict, local: dict) -> Tuple[Tuple[float, float], str, bool]:
        """Direction, ml/mr/mu/md event, and whether this frame is recordable for BrainLink."""
        x, y = 0.0, 0.0
        event = ""
        send_to_brainlink = False

        left = recordable["left"] or local["left"]
        right = recordable["right"] or local["right"]
        up = recordable["up"] or local["up"]
        down = recordable["down"] or local["down"]

        if left:
            x -= 1
            event = "ml"
            send_to_brainlink = recordable["left"]
        elif right:
            x += 1
            event = "mr"
            send_to_brainlink = recordable["right"]
        elif up:
            y += 1
            event = "mu"
            send_to_brainlink = recordable["up"]
        elif down:
            y -= 1
            event = "md"
            send_to_brainlink = recordable["down"]

        if x != 0 and y != 0:
            length = (x * x + y * y) ** 0.5
            x /= length
            y /= length
        return ((x, y), event, send_to_brainlink)

    def get_movement_and_event(self) -> Tuple[Tuple[float, float], str, bool]:
        """
        Returns:
            ((x, y), event, recordable): recordable=False for keyboard_local-only input.
        """
        return self._movement_from_keys(self.keys_recordable, self.keys_local)

    def is_action_pressed(self) -> bool:
        return self.keys_recordable.get("action", False) or self.keys_local.get("action", False)

    def is_action_pressed_recordable(self) -> bool:
        return self.keys_recordable.get("action", False)

    def clear_state(self):
        for store in (self.keys_recordable, self.keys_local):
            for k in _ACTIONS:
                store[k] = False

    def rebind_keys(self):
        self._apply_key_bindings()

    def cleanup(self):
        self.ignoreAll()
        logger.debug("KeyboardInput cleaned up")
