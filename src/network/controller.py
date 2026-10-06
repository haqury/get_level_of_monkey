"""Hooks between Game loop and host/client transport."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from src.network.client import GameClient
from src.network.protocol import (
    MsgType,
    make_minigame_state,
    make_player_state,
    make_scene_change,
    make_start_game,
)
from src.network.server import GameServer
from src.network.session import MultiplayerSession, SessionRole
from src.network.spawns import spawn_for
from src.network.util import get_lan_ip

if TYPE_CHECKING:
    from src.core.game import Game

logger = logging.getLogger(__name__)


class MultiplayerController:
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.session = MultiplayerSession()
        self.server: Optional[GameServer] = None
        self.client: Optional[GameClient] = None
        self.remote_player = None
        self._state_seq = 0
        self._send_accum = 0.0
        self._minigame_accum = 0.0
        self._host_waiting_in_menu = False
        self._client_waiting_start = False
        self._applying_remote_scene = False

        mp_cfg = game.game_config.get("multiplayer", {})
        self.tick_rate_hz = float(mp_cfg.get("tick_rate_hz", 20))
        self.default_port = int(mp_cfg.get("default_port", 17777))
        self.connect_timeout_sec = float(mp_cfg.get("connect_timeout_sec", 10))
        self.minigame_sync_hz = float(mp_cfg.get("minigame_sync_hz", 10))

    @property
    def is_online(self) -> bool:
        return self.session.is_online

    @property
    def is_host(self) -> bool:
        return self.session.is_host

    @property
    def is_client(self) -> bool:
        return self.session.is_client

    def lan_ip(self) -> str:
        return get_lan_ip()

    def shutdown(self) -> None:
        if self.server:
            self.server.stop()
            self.server = None
        if self.client:
            self.client.stop()
            self.client = None
        self._destroy_remote_player()
        self.session.reset_offline()
        self._host_waiting_in_menu = False
        self._client_waiting_start = False

    def start_host(self, port: Optional[int] = None) -> tuple[bool, str]:
        self.shutdown()
        port = int(port or self.default_port)
        name = self._player_name()
        self.session.begin_host(name)
        self.server = GameServer(port, name, self.session.session_id)
        if not self.server.start():
            self.shutdown()
            return False, "bind failed"
        self._host_waiting_in_menu = True
        return True, f"{self.lan_ip()}:{port}"

    def join_host(self, host: str, port: Optional[int] = None) -> bool:
        self.shutdown()
        port = int(port or self.default_port)
        host = (host or "127.0.0.1").strip()
        self.session.begin_client()
        self.client = GameClient(connect_timeout_sec=self.connect_timeout_sec)
        if not self.client.connect(host, port, self._player_name()):
            self.shutdown()
            return False
        self._client_waiting_start = True
        return True

    def _player_name(self) -> str:
        return (
            self.game.game_config.get("player", {}).get("name") or "Player"
        )[:64]

    def _ensure_remote_player(self) -> None:
        if self.remote_player or not self.session.is_online:
            return
        from src.entities.remote_player import RemotePlayer

        rid = self.session.remote_player_id()
        sx, sz = spawn_for("cave", rid)
        self.remote_player = RemotePlayer(self.game, pos=(sx, sz), player_id=rid)
        self.remote_player.node.show()

    def _destroy_remote_player(self) -> None:
        if self.remote_player:
            self.remote_player.cleanup()
            self.remote_player = None

    def on_enter_game(self) -> None:
        self.game.player.is_local = True
        self.game.player.player_id = self.session.local_player_id()
        if self.session.is_online:
            self._ensure_remote_player()
            scene_id = self.game.scene_manager.get_current_scene_name() or "cave"
            self._teleport_local_to_spawn(scene_id)
            if self.remote_player:
                rx, rz = spawn_for(scene_id, self.session.remote_player_id())
                self.remote_player.set_position(rx, rz)
                self.remote_player.node.show()

    def _teleport_local_to_spawn(self, scene_id: str) -> None:
        if not self.session.is_online:
            return
        x, z = spawn_for(scene_id, self.session.local_player_id())
        self.game.player.set_position(x, z)

    def host_switch_scene(
        self,
        scene_id: str,
        reason: str = "",
        monkey_mode: Optional[str] = None,
        extra_kwargs: Optional[dict] = None,
    ) -> None:
        """Host-only: switch locally and notify client."""
        if not self.session.is_host:
            return
        kwargs = dict(extra_kwargs or {})
        if monkey_mode:
            kwargs["monkey_mode"] = monkey_mode
        self.game.scene_manager.switch_to(scene_id, self.game.player, **kwargs)
        self._teleport_local_to_spawn(scene_id)
        if self.remote_player:
            rx, rz = spawn_for(scene_id, self.session.remote_player_id())
            self.remote_player.set_position(rx, rz)
        lx, lz = spawn_for(scene_id, 0)
        rx, rz = spawn_for(scene_id, 1)
        msg = make_scene_change(scene_id, lx, lz, rx, rz, reason, monkey_mode)
        if self.server:
            self.server.broadcast(msg)

    def client_apply_scene_change(self, msg: dict[str, Any]) -> None:
        if not self.session.is_client:
            return
        self._applying_remote_scene = True
        try:
            scene_id = str(msg.get("scene_id", "cave"))
            monkey_mode = msg.get("monkey_mode")
            kwargs = {}
            if monkey_mode:
                kwargs["monkey_mode"] = monkey_mode
            self.game.scene_manager.switch_to(scene_id, self.game.player, **kwargs)
            sx = float(msg.get("spawn_x", 0))
            sz = float(msg.get("spawn_z", 0))
            self.game.player.set_position(sx, sz)
            if self.remote_player:
                self.remote_player.set_position(
                    float(msg.get("remote_spawn_x", 0)),
                    float(msg.get("remote_spawn_z", 0)),
                )
                self.remote_player.node.show()
            self.game.in_game = True
            self.game.hud.show()
        finally:
            self._applying_remote_scene = False

    def should_client_skip_exits(self) -> bool:
        return self.session.is_client

    def update(self, dt: float) -> None:
        self._drain_incoming()
        if not self.session.is_online or not self.game.in_game:
            return
        self._ensure_remote_player()
        if self.remote_player:
            self.remote_player.update_interpolation(dt)
            cur = self.game.scene_manager.get_current_scene_name()
            if getattr(self.remote_player, "_network_scene_id", None) == cur:
                self.remote_player.node.show()
            elif getattr(self.remote_player, "_network_scene_id", None):
                self.remote_player.node.hide()
        self._send_accum += dt
        interval = 1.0 / max(1.0, self.tick_rate_hz)
        if self._send_accum >= interval:
            self._send_accum = 0.0
            self._send_local_player_state()
        if self.session.is_host:
            self._minigame_accum += dt
            mg_interval = 1.0 / max(1.0, self.minigame_sync_hz)
            if self._minigame_accum >= mg_interval:
                self._minigame_accum = 0.0
                self._broadcast_minigame_state()

    def _send_local_player_state(self) -> None:
        p = self.game.player
        scene_id = self.game.scene_manager.get_current_scene_name() or "cave"
        self._state_seq += 1
        msg = make_player_state(
            self.session.local_player_id(),
            scene_id,
            p.position.x,
            p.position.z,
            p.facing_direction,
            p.is_sitting,
            self._state_seq,
        )
        if self.server:
            self.server.broadcast(msg)
        elif self.client:
            self.client.send(msg)

    def _broadcast_minigame_state(self) -> None:
        if self.game.scene_manager.get_current_scene_name() != "minigame":
            return
        scene = self.game.scene_manager.get_current_scene()
        if not scene or not hasattr(scene, "build_network_snapshot"):
            return
        snap = scene.build_network_snapshot()
        if self.server:
            self.server.broadcast(make_minigame_state(snap))

    def _drain_incoming(self) -> None:
        transport = self.server or self.client
        if not transport:
            return
        while True:
            try:
                msg = transport.incoming.get_nowait()
            except Exception:
                break
            self._handle_message(msg)

    def _handle_message(self, msg: dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == "_client_connected":
            self.session.mark_connected(str(msg.get("player_name", "")))
            self._ensure_remote_player()
            menu = self.game.scene_manager.loaded_scenes.get("main_menu")
            if menu and hasattr(menu, "update_multiplayer_status"):
                menu.update_multiplayer_status(
                    "connected", msg.get("player_name", "")
                )
            if self._host_waiting_in_menu:
                self._host_waiting_in_menu = False
                if self.server:
                    self.server.broadcast(make_start_game())
                self.game.start_game(multiplayer_already_started=True)
            return
        if mtype == "_connected":
            welcome = msg.get("welcome") or {}
            self.session.session_id = str(welcome.get("session_id", ""))
            self.session.player_id = int(welcome.get("player_id", 1))
            self.session.mark_connected(str(welcome.get("host_name", "")))
            menu = self.game.scene_manager.loaded_scenes.get("main_menu")
            if menu and hasattr(menu, "update_multiplayer_status"):
                menu.update_multiplayer_status("waiting_host", self.session.peer_name)
            return
        if mtype == "_peer_disconnected":
            reason = str(msg.get("reason", "disconnected"))
            self._on_disconnect(reason)
            return
        if mtype == "_connect_failed":
            self._on_disconnect(str(msg.get("reason", "connect failed")))
            return
        if mtype == MsgType.START_GAME:
            if self.session.is_client and self._client_waiting_start:
                self._client_waiting_start = False
                self.game.start_game(multiplayer_already_started=True)
            return
        if mtype == MsgType.SCENE_CHANGE:
            if self.session.is_client:
                self.client_apply_scene_change(msg)
            return
        if mtype == MsgType.PLAYER_STATE:
            self._apply_player_state(msg)
            return
        if mtype == MsgType.MINIGAME_STATE:
            if self.session.is_client:
                scene = self.game.scene_manager.get_current_scene()
                if scene and hasattr(scene, "apply_network_snapshot"):
                    scene.apply_network_snapshot(msg)
            return
        if mtype == MsgType.GOODBYE:
            self._on_disconnect(str(msg.get("reason", "goodbye")))

    def _apply_player_state(self, msg: dict[str, Any]) -> None:
        pid = int(msg.get("player_id", -1))
        if pid == self.session.local_player_id():
            return
        self._ensure_remote_player()
        if not self.remote_player:
            return
        self.remote_player.apply_network_state(
            float(msg.get("x", 0)),
            float(msg.get("z", 0)),
            str(msg.get("facing", "down")),
            bool(msg.get("is_sitting", False)),
            str(msg.get("scene_id", "")),
        )

    def _on_disconnect(self, reason: str) -> None:
        logger.warning("Multiplayer disconnected: %s", reason)
        was_online = self.session.is_online
        self.session.mark_disconnected(reason)
        if self.server:
            self.server.stop()
            self.server = None
        if self.client:
            self.client.stop()
            self.client = None
        self._destroy_remote_player()
        if was_online and self.game.in_game:
            self.game._multiplayer_return_to_menu(reason)
