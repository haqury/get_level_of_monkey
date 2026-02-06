"""
Ввод от BrainLink — подключение к клиенту, чтение событий, направление движения по предсказанию.
"""

import logging
from typing import Optional, Tuple
from src.integration import BrainLinkClient

logger = logging.getLogger(__name__)


class BrainLinkInput:
    """
    Обработка ввода от BrainLink: подключение, чтение события (ml/mr/mu/md/stop),
    направление движения (x, y). Не знает о клавиатуре.
    """

    def __init__(self, base, enabled: bool = True):
        self.base = base
        self.enabled = enabled
        self.brainlink: Optional[BrainLinkClient] = None
        self.last_event = ""

        if not enabled:
            logger.info("BrainLinkInput: disabled")
            return

        from src.integration import get_brainlink_client
        memory_name = "brainlink_data"
        if hasattr(base, 'brainlink_launcher') and getattr(base.brainlink_launcher, '_found_memory_name', None):
            memory_name = base.brainlink_launcher._found_memory_name
            logger.info("BrainLinkInput: using memory name %s", memory_name)

        self.brainlink = get_brainlink_client(memory_name)
        if not self.brainlink.connect():
            logger.warning("BrainLinkInput: connect failed, using keyboard only")
            self.enabled = False
        else:
            logger.info("BrainLinkInput: connected")

    def update(self) -> Tuple[str, Tuple[float, float]]:
        """
        Прочитать текущее событие и вернуть направление движения.
        Returns:
            (event, (x, y)): event — "ml"|"mr"|"mu"|"md"|"stop"|""; (x,y) — направление или (0,0).
        """
        event = ""
        x, y = 0.0, 0.0

        if not self.enabled or not self.brainlink:
            return ("", (0.0, 0.0))

        if not self.brainlink.is_connected():
            if not getattr(self, '_reconnect_logged', False):
                logger.warning("BrainLinkInput: disconnected, attempting reconnect...")
                self._reconnect_logged = True
            self.brainlink.connect()
            return ("", (0.0, 0.0))
        self._reconnect_logged = False

        event = self.brainlink.get_event() or ""

        if event == "ml":
            x = -1.0
            logger.info("🎮 [BrainLink] movement LEFT (x=%s, y=%s)", x, y)
        elif event == "mr":
            x = 1.0
            logger.info("🎮 [BrainLink] movement RIGHT (x=%s, y=%s)", x, y)
        elif event == "mu":
            y = 1.0
            logger.info("🎮 [BrainLink] movement UP (x=%s, y=%s)", x, y)
        elif event == "md":
            y = -1.0
            logger.info("🎮 [BrainLink] movement DOWN (x=%s, y=%s)", x, y)
        elif event == "stop":
            x, y = 0.0, 0.0
            logger.info("🎮 [BrainLink] STOP (x=%s, y=%s)", x, y)

        if event and event != self.last_event:
            logger.info("🧠 [BrainLink] event changed: '%s' -> '%s'", self.last_event, event)
        self.last_event = event

        return (event, (x, y))

    def get_event(self) -> str:
        if not self.brainlink:
            return ""
        return self.brainlink.get_event() or ""

    def is_connected(self) -> bool:
        return bool(self.brainlink and self.brainlink.is_connected())

    def get_ml_stats(self) -> Tuple[float, dict]:
        if not self.brainlink:
            return (0.0, {})
        return self.brainlink.get_ml_stats()

    def send_event_to_history(self, event_name: str) -> bool:
        if not self.brainlink:
            return False
        return self.brainlink.send_event_to_history(event_name)

    def send_event_for_ml_training(self, event_name: str) -> bool:
        if not self.brainlink:
            return False
        return self.brainlink.send_event_for_ml_training(event_name)

    def clear_state(self):
        self.last_event = ""

    def cleanup(self):
        if self.brainlink:
            self.brainlink.disconnect()
        logger.debug("BrainLinkInput cleaned up")
