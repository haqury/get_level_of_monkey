"""Multiplayer session state (offline / host / client)."""

from __future__ import annotations

from enum import Enum
from uuid import uuid4


class SessionRole(str, Enum):
    OFFLINE = "offline"
    HOST = "host"
    CLIENT = "client"


class MultiplayerSession:
    """Local view of multiplayer role and player id (0=host, 1=client)."""

    def __init__(self) -> None:
        self.role = SessionRole.OFFLINE
        self.player_id = 0
        self.session_id = ""
        self.peer_name = ""
        self.connected = False
        self.disconnect_reason = ""

    @property
    def is_online(self) -> bool:
        return self.role in (SessionRole.HOST, SessionRole.CLIENT) and self.connected

    @property
    def is_host(self) -> bool:
        return self.role == SessionRole.HOST and self.connected

    @property
    def is_client(self) -> bool:
        return self.role == SessionRole.CLIENT and self.connected

    def reset_offline(self) -> None:
        self.role = SessionRole.OFFLINE
        self.player_id = 0
        self.session_id = ""
        self.peer_name = ""
        self.connected = False
        self.disconnect_reason = ""

    def begin_host(self, host_name: str) -> None:
        self.role = SessionRole.HOST
        self.player_id = 0
        self.session_id = uuid4().hex[:12]
        self.peer_name = ""
        self.connected = False
        self.disconnect_reason = ""
        self._local_name = host_name

    def begin_client(self) -> None:
        self.role = SessionRole.CLIENT
        self.player_id = 1
        self.session_id = ""
        self.peer_name = ""
        self.connected = False
        self.disconnect_reason = ""

    def mark_connected(self, peer_name: str = "") -> None:
        self.connected = True
        if peer_name:
            self.peer_name = peer_name

    def mark_disconnected(self, reason: str = "") -> None:
        self.connected = False
        self.disconnect_reason = reason or "disconnected"

    def local_player_id(self) -> int:
        return self.player_id

    def remote_player_id(self) -> int:
        return 1 if self.player_id == 0 else 0
