"""Multiplayer spawn points per scene (host index 0, client index 1)."""

from __future__ import annotations

MULTIPLAYER_SPAWN: dict[str, list[tuple[float, float]]] = {
    "cave": [(0.0, 0.0), (-4.0, 0.0)],
    "kitchen": [(10.0, 0.0), (6.0, 0.0)],
    "minigame": [(0.0, 0.0), (2.0, 0.0)],
    "main_menu": [(0.0, 0.0), (0.0, 0.0)],
}


def spawn_for(scene_id: str, player_id: int) -> tuple[float, float]:
    points = MULTIPLAYER_SPAWN.get(scene_id, [(0.0, 0.0), (0.0, 0.0)])
    idx = 0 if player_id == 0 else 1
    if idx >= len(points):
        idx = 0
    return points[idx]
