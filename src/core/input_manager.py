"""
Input Manager — объединяет клавиатурный ввод и ввод от BrainLink, задаёт приоритет и отправку в BrainLink.
"""

import logging
from typing import Optional, Tuple
from direct.showbase.DirectObject import DirectObject

from src.core.keyboard_input import KeyboardInput
from src.core.brainlink_input import BrainLinkInput

logger = logging.getLogger(__name__)

MOVEMENT_SOURCE_NONE = "none"
MOVEMENT_SOURCE_KEYBOARD = "keyboard"
MOVEMENT_SOURCE_BRAINLINK = "brainlink"


class InputManager(DirectObject):
    """
    Оркестратор ввода: клавиатура имеет приоритет над BrainLink.
    Отправка в BrainLink (history/ML) только при действиях с клавиатуры.
    """

    def __init__(self, base, brainlink_enabled: bool = True):
        super().__init__()
        self.base = base
        self.keyboard = KeyboardInput(base)
        self.brainlink_input = BrainLinkInput(base, enabled=brainlink_enabled)

        # Для совместимости: доступ к клиенту BrainLink как input_manager.brainlink
        self.brainlink = self.brainlink_input.brainlink

        self.move_direction = (0.0, 0.0)
        self.action_pressed = False

        self._current_movement_event = ""
        self._movement_source = MOVEMENT_SOURCE_NONE
        self._current_keyboard_event = ""
        self._is_using_brainlink = False
        self._current_ml_event = ""
        self.last_keyboard_event = ""
        self._last_sent_event = ""  # последнее отправленное в BrainLink (ml/mr/mu/md/ne)

        self.send_keyboard_events = False
        self.send_brainlink_events = False
        self.send_to_history = False
        self.send_to_ml = False

        if hasattr(base, 'game_config'):
            bl_config = base.game_config.get("brainlink", {})
            self.send_keyboard_events = bl_config.get("send_keyboard_events", True)
            self.send_brainlink_events = bl_config.get("send_brainlink_events", True)
            self.send_to_history = bl_config.get("send_to_history", True)
            self.send_to_ml = bl_config.get("send_to_ml", False)

        logger.info(
            "🎮 InputManager initialized (BrainLink: %s, send_keyboard: %s, send_to_history: %s, send_to_ml: %s)",
            brainlink_enabled, self.send_keyboard_events, self.send_to_history, self.send_to_ml,
        )

    @property
    def on_action(self):
        return self.keyboard.on_action

    @on_action.setter
    def on_action(self, value):
        self.keyboard.on_action = value

    @property
    def on_sit_pause(self):
        return self.keyboard.on_sit_pause

    @on_sit_pause.setter
    def on_sit_pause(self, value):
        self.keyboard.on_sit_pause = value

    def update(self, dt: float):
        (kb_dir, kb_event) = self.keyboard.get_movement_and_event()
        bl_event, bl_dir = self.brainlink_input.update()
        self._current_ml_event = bl_event or ""

        # Приоритет: клавиатура > BrainLink
        if kb_event:
            x, y = kb_dir
            movement_from_brainlink_this_frame = False
            self._current_movement_event = kb_event
            self._movement_source = MOVEMENT_SOURCE_KEYBOARD
            self._current_keyboard_event = kb_event
            self._is_using_brainlink = False
        elif bl_event:
            x, y = bl_dir
            movement_from_brainlink_this_frame = True
            self._current_movement_event = bl_event
            self._movement_source = MOVEMENT_SOURCE_BRAINLINK
            self._current_keyboard_event = ""
            self._is_using_brainlink = bool(bl_event != "stop")
        else:
            x, y = 0.0, 0.0
            movement_from_brainlink_this_frame = False
            self._current_movement_event = ""
            self._movement_source = MOVEMENT_SOURCE_NONE
            self._current_keyboard_event = ""
            self._is_using_brainlink = False

        if kb_event:
            self.last_keyboard_event = kb_event
        else:
            self.last_keyboard_event = ""

        # Нормализация диагонали
        if x != 0 and y != 0:
            length = (x * x + y * y) ** 0.5
            x /= length
            y /= length

        self.move_direction = (x, y)
        self.action_pressed = self.keyboard.is_action_pressed()

        # Отправка в BrainLink текущего эффективного действия (клавиатура или BrainLink); при остановке — "ne"
        if self.brainlink and self.brainlink.is_connected() and (self.send_to_history or self.send_to_ml):
            if x < 0 and y == 0:
                effective_event = "ml"
            elif x > 0 and y == 0:
                effective_event = "mr"
            elif y > 0 and x == 0:
                effective_event = "mu"
            elif y < 0 and x == 0:
                effective_event = "md"
            else:
                effective_event = "ne"
            allow_send = (
                effective_event == "ne"
                or (self._movement_source == MOVEMENT_SOURCE_KEYBOARD and self.send_keyboard_events)
                or (self._movement_source == MOVEMENT_SOURCE_BRAINLINK and self.send_brainlink_events)
            )
            if allow_send and effective_event != self._last_sent_event:
                self._last_sent_event = effective_event
                if self.send_to_ml:
                    self.brainlink_input.send_event_for_ml_training(effective_event)
                elif self.send_to_history:
                    self.brainlink_input.send_event_to_history(effective_event)
                logger.debug("📤 Sent effective event '%s' to BrainLink", effective_event)

    def clear_state(self):
        """Сброс ввода (диалог/смена сцены). В BrainLink «stop» не отправляется — только при явном «сидеть» (Space)."""
        self.keyboard.clear_state()
        self.brainlink_input.clear_state()
        self.last_keyboard_event = ""
        self._last_sent_event = ""
        self.move_direction = (0.0, 0.0)
        self.action_pressed = False
        self._current_movement_event = ""
        self._movement_source = MOVEMENT_SOURCE_NONE

    def get_movement(self) -> Tuple[float, float]:
        return self.move_direction

    def rebind_keys(self):
        self.keyboard.rebind_keys()

    def is_action_pressed(self) -> bool:
        return self.action_pressed

    def is_using_brainlink(self) -> bool:
        return getattr(self, '_is_using_brainlink', False)

    def get_current_keyboard_event(self) -> str:
        return getattr(self, '_current_keyboard_event', "")

    def get_movement_source(self) -> str:
        return getattr(self, '_movement_source', MOVEMENT_SOURCE_NONE)

    def get_current_movement_event_with_source(self) -> Tuple[str, str]:
        return (
            getattr(self, '_current_movement_event', ""),
            getattr(self, '_movement_source', MOVEMENT_SOURCE_NONE),
        )

    def get_ml_display_info(self) -> tuple:
        pred = getattr(self, '_current_ml_event', "") or "—"
        connected = self.brainlink_input.is_connected()
        confidence, probs = self.brainlink_input.get_ml_stats()
        return (pred, connected, confidence, probs)

    def cleanup(self):
        self.keyboard.cleanup()
        self.brainlink_input.cleanup()
        logger.info("InputManager cleaned up")
