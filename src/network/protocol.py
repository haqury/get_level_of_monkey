"""JSON-line protocol for 2-player coop."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Optional

PROTOCOL_VERSION = 1


class MsgType(StrEnum):
    HELLO = "hello"
    WELCOME = "welcome"
    GOODBYE = "goodbye"
    START_GAME = "start_game"
    PLAYER_STATE = "player_state"
    SCENE_CHANGE = "scene_change"
    DIALOG_EVENT = "dialog_event"
    MINIGAME_STATE = "minigame_state"
    PING = "ping"
    PONG = "pong"


def encode_message(msg: dict[str, Any]) -> bytes:
    line = json.dumps(msg, separators=(",", ":"), ensure_ascii=False)
    return (line + "\n").encode("utf-8")


def decode_line(line: str) -> Optional[dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        return None
    return None


def make_hello(player_name: str) -> dict[str, Any]:
    return {
        "type": MsgType.HELLO,
        "protocol_version": PROTOCOL_VERSION,
        "player_name": player_name[:64],
    }


def make_welcome(session_id: str, player_id: int, host_name: str) -> dict[str, Any]:
    return {
        "type": MsgType.WELCOME,
        "protocol_version": PROTOCOL_VERSION,
        "session_id": session_id,
        "player_id": player_id,
        "host_name": host_name[:64],
    }


def make_goodbye(reason: str = "") -> dict[str, Any]:
    return {"type": MsgType.GOODBYE, "reason": reason[:256]}


def make_start_game() -> dict[str, Any]:
    return {"type": MsgType.START_GAME}


def make_player_state(
    player_id: int,
    scene_id: str,
    x: float,
    z: float,
    facing: str,
    is_sitting: bool,
    seq: int,
) -> dict[str, Any]:
    return {
        "type": MsgType.PLAYER_STATE,
        "player_id": player_id,
        "scene_id": scene_id,
        "x": round(x, 3),
        "z": round(z, 3),
        "facing": facing,
        "is_sitting": bool(is_sitting),
        "seq": int(seq),
    }


def make_scene_change(
    scene_id: str,
    spawn_x: float,
    spawn_z: float,
    remote_spawn_x: float,
    remote_spawn_z: float,
    reason: str = "",
    monkey_mode: Optional[str] = None,
) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "type": MsgType.SCENE_CHANGE,
        "scene_id": scene_id,
        "spawn_x": spawn_x,
        "spawn_z": spawn_z,
        "remote_spawn_x": remote_spawn_x,
        "remote_spawn_z": remote_spawn_z,
        "reason": reason[:128],
    }
    if monkey_mode:
        msg["monkey_mode"] = monkey_mode
    return msg


def make_minigame_state(payload: dict[str, Any]) -> dict[str, Any]:
    out = {"type": MsgType.MINIGAME_STATE}
    out.update(payload)
    return out


def make_dialog_event(npc_id: str, line_index: int) -> dict[str, Any]:
    return {
        "type": MsgType.DIALOG_EVENT,
        "npc_id": npc_id,
        "line_index": int(line_index),
    }
