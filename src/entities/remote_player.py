"""Second player rendered from network state (no local input)."""

import logging

from src.entities.player import Player

logger = logging.getLogger(__name__)


class RemotePlayer(Player):
    """Remote coop player — position driven by network interpolation."""

    def __init__(self, base, pos=(0, 0), player_id: int = 1):
        super().__init__(base, pos=pos)
        self.is_local = False
        self.player_id = player_id
        self._target_x = pos[0]
        self._target_z = pos[1]
        self._lerp_speed = 12.0
        if self.node:
            self.node.setColor(1.0, 0.55, 0.35, 1.0)

    def apply_network_state(
        self,
        x: float,
        z: float,
        facing: str,
        is_sitting: bool,
        scene_id: str | None = None,
    ) -> None:
        self._target_x = x
        self._target_z = z
        if facing in ("up", "down", "left", "right"):
            if self.facing_direction != facing:
                self.facing_direction = facing
                self._update_sprite()
        self.is_sitting = is_sitting
        self._network_scene_id = scene_id

    def update_interpolation(self, dt: float) -> None:
        """Smooth toward last received position."""
        ax = self.position.x
        az = self.position.z
        tx, tz = self._target_x, self._target_z
        t = min(1.0, self._lerp_speed * dt)
        nx = ax + (tx - ax) * t
        nz = az + (tz - az) * t
        if abs(nx - ax) > 0.001 or abs(nz - az) > 0.001:
            self.is_moving = True
            self.set_position(nx, nz)
        else:
            self.is_moving = False
        if self.is_sitting:
            self.node.setScale(1, 1, 0.75)
        else:
            self.node.setScale(1, 1, 1)
