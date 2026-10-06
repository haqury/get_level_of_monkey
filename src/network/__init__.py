"""Multiplayer networking (host / client, JSON lines over TCP)."""

from src.network.session import MultiplayerSession, SessionRole
from src.network.protocol import PROTOCOL_VERSION, MsgType

__all__ = [
    "MultiplayerSession",
    "SessionRole",
    "PROTOCOL_VERSION",
    "MsgType",
]
