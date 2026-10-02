"""Minigame - Monkey Attack"""

import logging
import random
from panda3d.core import CardMaker, Vec3, TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel
from src.scenes.base_scene import BaseScene
from src.core.i18n import t

logger = logging.getLogger(__name__)


# Clearing and road constants (used by Monkey, Poop, MinigameScene)
CLEARING_HALF_W = 30.0   # clearing 60x30, half width
CLEARING_HALF_H = 15.0   # half height
ROAD_WIDTH = 2.5         # road strip width; player cannot step on road


class Monkey:
    """Обезьяна в мини-игре"""
    
    def __init__(self, base, age: int, pos: tuple, stats: dict, walk_direction: str = "horizontal", monkey_mode: str = "NorthSouth", base_poop_speed: float = 20.0, initial_direction: tuple = None):
        """
        Args:
            base: ShowBase
            age: Возраст обезьяны (1-4)
            pos: Позиция (x, y) — can be in forest so monkey walks out onto path
            stats: Характеристики (throw_speed, accuracy, cooldown)
            walk_direction: "horizontal" or "vertical" - direction along edge
            monkey_mode: "NorthSouth" or "WestEast" - determines movement pattern
            base_poop_speed: Base speed for thrown poop
            initial_direction: Optional (dx, dz) so monkey walks from forest onto path
        """
        self.base = base
        self.age = age
        self.position = Vec3(pos[0], 0, pos[1])
        self.stats = stats
        self.walk_direction = walk_direction
        self.monkey_mode = monkey_mode
        self.base_poop_speed = base_poop_speed
        
        # Throwing state — reduced cooldown so monkeys shoot more often
        self.throw_cooldown = 0
        self.max_cooldown = max(0.5, stats["cooldown"] * 0.4)  # ~0.6–1.2 s instead of 1.5–3 s
        
        # Movement state - monkeys walk along forest edge
        self.move_speed = random.uniform(3.0, 6.0)  # Speed along edge
        
        if initial_direction is not None:
            self.move_direction = Vec3(initial_direction[0], 0, initial_direction[1])
        elif monkey_mode == "NorthSouth":
            direction = random.choice([-1, 1])
            self.move_direction = Vec3(direction, 0, 0)
        else:
            direction = random.choice([-1, 1])
            self.move_direction = Vec3(0, 0, direction)
        
        self.move_direction.normalize()
        
        # Visual
        self.node = self._create_visual()
        self.node.reparentTo(base.render)
        self.node.setPos(self.position)
    
    def _create_visual(self):
        """Create monkey visual with sprite"""
        from pathlib import Path
        
        cm = CardMaker(f"monkey_{self.age}")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        
        node = self.base.render.attachNewNode(cm.generate())
        
        # Try to load sprite
        sprite_path = Path(f"assets/sprites/monkey/age{self.age}.png")
        if sprite_path.exists():
            try:
                texture = self.base.loader.loadTexture(str(sprite_path))
                node.setTexture(texture)
                node.setTwoSided(True)
            except Exception as e:
                logger.warning(f"Could not load monkey sprite: {e}")
                # Fallback to color
                colors = [
                    (0.8, 0.6, 0.3),  # Age 1 - light brown
                    (0.6, 0.4, 0.2),  # Age 2
                    (0.5, 0.3, 0.1),  # Age 3
                    (0.3, 0.2, 0.1),  # Age 4 - dark brown
                ]
                node.setColor(*colors[self.age - 1], 1.0)
        else:
            # Fallback to color
            colors = [
                (0.8, 0.6, 0.3),  # Age 1 - light brown
                (0.6, 0.4, 0.2),  # Age 2
                (0.5, 0.3, 0.1),  # Age 3
                (0.3, 0.2, 0.1),  # Age 4 - dark brown
            ]
            node.setColor(*colors[self.age - 1], 1.0)
        
        node.setBillboardPointEye()
        # Always render on top of clearing/road/bushes
        node.setBin("fixed", 30)
        node.setDepthTest(False)
        node.setDepthWrite(False)
        
        return node
    
    def update(self, dt: float, player_pos: tuple):
        """Update monkey - walk along forest edge and throw poop when perpendicular to player"""
        # Move monkey along edge
        movement = self.move_direction * self.move_speed * dt
        new_x = self.position.x + movement.x
        new_y = self.position.z + movement.z
        
        # Keep monkeys on edge - if they reach the end, despawn (monkey goes into forest)
        edge_offset_x = CLEARING_HALF_W
        edge_offset_y = CLEARING_HALF_H
        
        if self.monkey_mode == "NorthSouth":
            # Monkeys walk along top/bottom edge (horizontal movement)
            # Keep y position on edge (top or bottom)
            if abs(self.position.z) > edge_offset_y + 1 or abs(self.position.z) < edge_offset_y - 1:
                # Keep on edge - snap to top or bottom edge
                if self.position.z > 0:
                    new_y = edge_offset_y  # Top edge
                else:
                    new_y = -edge_offset_y  # Bottom edge
            
            # Despawn only when leaving path at the far end (monkeys spawn in forest at near end)
            if self.move_direction.x > 0 and new_x > CLEARING_HALF_W:
                return "despawn"  # Walked off right into forest
            if self.move_direction.x < 0 and new_x < -CLEARING_HALF_W:
                return "despawn"  # Walked off left into forest
        else:  # WestEast
            # Monkeys walk along left/right edge (vertical movement)
            # Keep x position on edge (left or right)
            if abs(self.position.x) > edge_offset_x + 1 or abs(self.position.x) < edge_offset_x - 1:
                # Keep on edge - snap to left or right edge
                if self.position.x > 0:
                    new_x = edge_offset_x  # Right edge
                else:
                    new_x = -edge_offset_x  # Left edge
            
            # Despawn only when leaving path at the far end
            if self.move_direction.z > 0 and new_y > CLEARING_HALF_H:
                return "despawn"  # Walked off top into forest
            if self.move_direction.z < 0 and new_y < -CLEARING_HALF_H:
                return "despawn"  # Walked off bottom into forest
        
        # Apply movement
        self.position.x = new_x
        self.position.z = new_y
        # Keep Y at 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
        self.node.setPos(self.position.x, 1.0, self.position.z)
        
        # Throw only when perpendicular to monkey's path (player in same row/column band)
        # Threshold 15 ≈ full playable height/width so monkeys shoot often when player is in range
        PERPENDICULAR_THRESHOLD = 15.0
        in_playable = (
            abs(player_pos[0]) <= CLEARING_HALF_W - ROAD_WIDTH
            and abs(player_pos[1]) <= CLEARING_HALF_H - ROAD_WIDTH
        )
        can_throw = False
        if in_playable:
            if self.monkey_mode == "NorthSouth":
                if abs(self.position.z - player_pos[1]) < PERPENDICULAR_THRESHOLD:
                    can_throw = True
            else:  # WestEast
                if abs(self.position.x - player_pos[0]) < PERPENDICULAR_THRESHOLD:
                    can_throw = True
        
        # Update throwing cooldown
        self.throw_cooldown -= dt
        
        # Can throw? Only when perpendicular to player
        if can_throw and self.throw_cooldown <= 0:
            self.throw_cooldown = self.max_cooldown
            return self._throw_poop(player_pos)
        
        return None
    
    def _throw_poop(self, player_pos: tuple):
        """Throw poop strictly perpendicular to path: from edge straight inward (no component along path)."""
        accuracy_spread = random.uniform(-3, 3) * (1 - self.stats["accuracy"])
        speed = self.base_poop_speed * self.stats["throw_speed"] * 0.8  # 20% slower
        # NorthSouth: path is horizontal (along x). Perpendicular = straight in z (down from top, up from bottom).
        if self.monkey_mode == "NorthSouth":
            target_x = self.position.x  # same column — no horizontal component
            target_y = player_pos[1] + accuracy_spread
        # WestEast: path is vertical (along z). Perpendicular = straight in x (right from left, left from right).
        else:
            target_x = player_pos[0] + accuracy_spread
            target_y = self.position.z  # same row — no vertical component
        return Poop(self.base, self.position.x, self.position.z, target_x, target_y, speed)
    
    def cleanup(self):
        """Cleanup"""
        if self.node:
            self.node.removeNode()


class Poop:
    """Какашка (снаряд)"""
    
    def __init__(self, base, start_x: float, start_y: float, target_x: float, target_y: float, speed: float):
        """
        Args:
            base: ShowBase
            start_x, start_y: Starting position
            target_x, target_y: Target position
            speed: Flight speed multiplier
        """
        self.base = base
        self.position = Vec3(start_x, 0, start_y)
        
        # Calculate velocity
        dx = target_x - start_x
        dy = target_y - start_y
        dist = (dx*dx + dy*dy) ** 0.5
        
        if dist > 0:
            self.velocity = Vec3(dx / dist * speed, 0, dy / dist * speed)
        else:
            self.velocity = Vec3(0, 0, 0)
        
        # Lifetime
        self.lifetime = 5.0
        self.is_alive = True
        
        # Visual
        self.node = self._create_visual()
        self.node.reparentTo(base.render)
        self.node.setPos(self.position)
    
    def _create_visual(self):
        """Create poop visual with sprite"""
        from pathlib import Path
        
        cm = CardMaker("poop")
        cm.setFrame(-0.25, 0.25, -0.25, 0.25)
        
        node = self.base.render.attachNewNode(cm.generate())
        
        # Try to load sprite
        sprite_path = Path("assets/sprites/minigame/poop.png")
        if sprite_path.exists():
            try:
                texture = self.base.loader.loadTexture(str(sprite_path))
                node.setTexture(texture)
                node.setTwoSided(True)
            except Exception as e:
                logger.warning(f"Could not load poop sprite: {e}")
                # Fallback to color
                node.setColor(0.4, 0.25, 0.13, 1.0)  # Brown
        else:
            # Fallback to color
            node.setColor(0.4, 0.25, 0.13, 1.0)  # Brown
        
        node.setBillboardPointEye()
        # Render on top of clearing/road/bushes so poop is visible
        node.setBin("fixed", 40)
        node.setDepthTest(False)
        node.setDepthWrite(False)
        
        return node
    
    def update(self, dt: float):
        """Update poop position. Poop that misses flies to forest and disappears."""
        if not self.is_alive:
            return
        
        # Move
        self.position += self.velocity * dt
        # Keep Y at 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
        self.node.setPos(self.position.x, 1.0, self.position.z)
        
        # Poop that reaches forest boundary disappears
        if abs(self.position.x) > CLEARING_HALF_W or abs(self.position.z) > CLEARING_HALF_H:
            self.is_alive = False
            return
        
        # Lifetime fallback
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_alive = False
    
    def check_collision(self, player_pos: tuple, radius: float = 0.5) -> bool:
        """Check collision with player"""
        if not self.is_alive:
            return False
        
        dx = player_pos[0] - self.position.x
        dy = player_pos[1] - self.position.z
        dist = (dx*dx + dy*dy) ** 0.5
        
        if dist < radius:
            self.is_alive = False
            return True
        
        return False
    
    def cleanup(self):
        """Cleanup"""
        if self.node:
            self.node.removeNode()


class MinigameScene(BaseScene):
    """Мини-игра 'Обезьянья атака'"""
    
    # Monkey movement modes (determines where monkeys walk)
    # NorthSouth: monkeys walk from left and right edges (along top/bottom)
    # WestEast: monkeys walk from top and bottom edges (along left/right)
    
    # Movement area bounds - player restricted to clearing minus road (cannot step on road)
    # Clearing 60x30; road strip ROAD_WIDTH at edges; playable inner rect
    MOVEMENT_BOUNDS = {
        "min_x": -CLEARING_HALF_W + ROAD_WIDTH,
        "max_x": CLEARING_HALF_W - ROAD_WIDTH,
        "min_y": -CLEARING_HALF_H + ROAD_WIDTH,
        "max_y": CLEARING_HALF_H - ROAD_WIDTH
    }
    
    def __init__(self, base, balance_config: dict):
        super().__init__(base, "Minigame")
        
        self.balance = balance_config["minigame"]
        
        # Poop base speed from config (throw_speed is multiplier; e.g. 300/15 = 20 units/sec base)
        self._poop_base_speed = float(self.balance.get("poop", {}).get("speed", 300)) / 15.0
        
        # Game state
        self.monkeys = []
        self.poops = []
        self.game_time = 0
        self.is_game_over = False
        self.monkey_mode = None  # "NorthSouth" or "WestEast" - determines monkey movement pattern
        
        # Spawn: next group only when current group reached forest; size 1→2→…→5; cap 5 for 30s
        self._spawn_group_size = 1
        self._cap_5_until_time = None
        
        # Visual elements
        self.clearing = None  # Поляна
        self.bushes = []  # Кусты
        self.roads = []   # Road strips where monkeys walk (player cannot step on)
        
        # Create background
        self._create_background()
        
        # Create exit (to cave) - 5x position
        self.exits.append({
            "name": "to_cave",
            "pos": (0, -25),  # -5 * 5
            "target_scene": "cave",
            "text": "Exit"
        })
        
        logger.info("Minigame scene created")
    
    def _create_background(self):
        """Create minigame background - forest floor
        Uses cave dimensions as base: -35 to 35 (width), -18 to 18 (height)
        """
        from pathlib import Path
        from panda3d.core import TextureStage, Texture
        
        # Background matches cave dimensions exactly
        cm = CardMaker("minigame_bg")
        cm.setFrame(-35, 35, -18, 18)  # Same as cave dimensions
        
        self.background = self.base.render.attachNewNode(cm.generate())
        self.background.setPos(0, 0.5, 0)  # Lower Y position for background
        
        # Try to load forest floor sprite
        forest_floor_path = Path("assets/sprites/minigame/forest_floor.png")
        if forest_floor_path.exists():
            try:
                forest_floor_texture = self.base.loader.loadTexture(str(forest_floor_path))
                forest_floor_texture.setWrapU(Texture.WMRepeat)
                forest_floor_texture.setWrapV(Texture.WMRepeat)
                ts = TextureStage('default')
                self.background.setTexture(ts, forest_floor_texture)
                # Tile texture: larger setTexScale = more repeats (frame 70x36 units)
                self.background.setTexScale(ts, 70.0, 36.0)
                logger.info(f"Loaded forest floor sprite from: {forest_floor_path}")
            except Exception as e:
                logger.warning(f"Could not load forest floor sprite: {e}")
                self.background.setColor(0.25, 0.4, 0.15, 1.0)  # Fallback color
        else:
            # Fallback to color
            self.background.setColor(0.25, 0.4, 0.15, 1.0)  # Medium dark green (forest floor)
        
        self.background.setBillboardPointEye()
        self.background.setTwoSided(True)
        self.background.setDepthTest(False)
        self.background.setDepthWrite(False)
    
    def _create_clearing_and_bushes(self, monkey_mode: str):
        """Create clearing (поляна) in center and bushes around edges
        
        Args:
            monkey_mode: "NorthSouth" or "WestEast" - determines where monkeys walk
        """
        # Clean up old elements
        if self.clearing:
            self.clearing.removeNode()
        for bush in self.bushes:
            bush.removeNode()
        self.bushes.clear()
        for road in self.roads:
            road.removeNode()
        self.roads.clear()
        
        # Clearing size - playable area using cave dimensions as base
        # Cave is -35 to 35 (width 70), -18 to 18 (height 36)
        # Playable area should be larger - most of the space, with thin forest on edges
        # Make clearing much larger: ~85% of cave dimensions
        clearing_size_x = 60.0  # Width - much larger (was 30.0)
        clearing_size_y = 30.0  # Height - much larger (was 14.0)
        
        # Clearing always in center (player spawns here)
        clearing_center = (0, 0)
        
        # Create visible forest boundaries around edges
        # Forest should be at cave boundaries (-35 to 35, -18 to 18)
        # Forest thickness should fill the space between clearing and cave edges
        # With larger clearing (60x30), forest will be thinner but still visible
        forest_thickness_left = max(2.0, 35 - clearing_size_x/2)  # At least 2 units thick
        forest_thickness_right = max(2.0, 35 - clearing_size_x/2)
        forest_thickness_top = max(2.0, 18 - clearing_size_y/2)  # At least 2 units thick
        forest_thickness_bottom = max(2.0, 18 - clearing_size_y/2)
        
        bush_positions = [
            # Top forest wall (north) - from clearing top to cave top
            (0, clearing_size_y/2 + forest_thickness_top/2, 70, forest_thickness_top),
            # Bottom forest wall (south) - from clearing bottom to cave bottom
            (0, -clearing_size_y/2 - forest_thickness_bottom/2, 70, forest_thickness_bottom),
            # Left forest wall (west) - from clearing left to cave left
            (-clearing_size_x/2 - forest_thickness_left/2, 0, forest_thickness_left, 36),
            # Right forest wall (east) - from clearing right to cave right
            (clearing_size_x/2 + forest_thickness_right/2, 0, forest_thickness_right, 36),
        ]
        
        # Create clearing (clearing) - light grass in center (playable area)
        # Try to load clearing sprite
        from pathlib import Path
        from panda3d.core import TextureStage, Texture
        
        # Try to load clearing sprite, fallback to floor sprite
        clearing_sprite_path = Path("assets/sprites/minigame/clearing.png")
        clearing_texture = None
        if clearing_sprite_path.exists():
            try:
                clearing_texture = self.base.loader.loadTexture(str(clearing_sprite_path))
                logger.info(f"Loaded clearing sprite from: {clearing_sprite_path}")
            except Exception as e:
                logger.warning(f"Could not load clearing sprite: {e}")
        
        # Fallback to floor sprite if clearing sprite doesn't exist
        if not clearing_texture:
            floor_sprite_path = Path("assets/sprites/tiles/floor.png")
            if floor_sprite_path.exists():
                try:
                    clearing_texture = self.base.loader.loadTexture(str(floor_sprite_path))
                    logger.info(f"Using floor sprite as clearing texture")
                except Exception as e:
                    logger.debug(f"Could not load floor sprite: {e}")
        
        cm_clearing = CardMaker("clearing")
        cm_clearing.setFrame(-clearing_size_x/2, clearing_size_x/2, -clearing_size_y/2, clearing_size_y/2)
        self.clearing = self.base.render.attachNewNode(cm_clearing.generate())
        self.clearing.setPos(clearing_center[0], 0.6, clearing_center[1])  # Above background but below characters
        
        if clearing_texture:
            # Apply tiled texture (repeat, not stretch): larger scale = more repeats
            ts = TextureStage('default')
            clearing_texture.setWrapU(Texture.WMRepeat)
            clearing_texture.setWrapV(Texture.WMRepeat)
            self.clearing.setTexture(ts, clearing_texture)
            self.clearing.setTexScale(ts, clearing_size_x, clearing_size_y)
        else:
            # Fallback to color
            self.clearing.setColor(0.5, 0.7, 0.4, 1.0)  # Light green (clearing)
        
        self.clearing.setBillboardPointEye()
        self.clearing.setTwoSided(True)
        # Set render order - clearing should be above background
        self.clearing.setBin("fixed", 10)  # Render after background
        self.clearing.setDepthTest(False)  # Ensure visibility
        self.clearing.setDepthWrite(False)
        logger.info(f"Created clearing at ({clearing_center[0]}, {clearing_center[1]}), size ({clearing_size_x}, {clearing_size_y}), texture={clearing_texture is not None}")
        self.clearing.setDepthTest(False)  # Ensure visibility
        self.clearing.setDepthWrite(False)
        
        # Create road strips where monkeys walk (player cannot step on road)
        self._create_road(clearing_size_x, clearing_size_y)
        
        # Create forest walls (bushes) - dark green forest boundaries
        # Try to load forest sprite
        forest_sprite_path = Path("assets/sprites/minigame/forest.png")
        forest_texture = None
        if forest_sprite_path.exists():
            try:
                forest_texture = self.base.loader.loadTexture(str(forest_sprite_path))
                logger.info(f"Loaded forest sprite from: {forest_sprite_path}")
            except Exception as e:
                logger.warning(f"Could not load forest sprite: {e}")
        
        # Fallback to wall sprites if forest sprite not found
        if not forest_texture:
            fallback_paths = [
                Path("assets/sprites/cave/cave_wall.png"),  # Prefer cave wall
                Path("assets/sprites/tiles/wall.png"),
            ]
            for sprite_path in fallback_paths:
                if sprite_path.exists():
                    try:
                        forest_texture = self.base.loader.loadTexture(str(sprite_path))
                        logger.info(f"Using fallback forest texture from: {sprite_path}")
                        break
                    except Exception as e:
                        logger.debug(f"Could not load fallback texture from {sprite_path}: {e}")
        
        # Make them more visible with darker color and proper positioning
        for i, (x, y, w, h) in enumerate(bush_positions):
            cm_bush = CardMaker(f"forest_wall_{i}")
            cm_bush.setFrame(-w/2, w/2, -h/2, h/2)
            bush = self.base.render.attachNewNode(cm_bush.generate())
            bush.setPos(x, 0.7, y)  # Above clearing but below characters
            
            # Apply texture if available, otherwise use color
            if forest_texture:
                ts = TextureStage('default')
                forest_texture.setWrapU(Texture.WMRepeat)
                forest_texture.setWrapV(Texture.WMRepeat)
                bush.setTexture(ts, forest_texture)
                # Tile texture (repeat): scale = size in world units
                bush.setTexScale(ts, w, h)
            else:
                # Very dark green for forest - more visible boundary
                # Make it darker and more distinct
                bush.setColor(0.1, 0.25, 0.05, 1.0)  # Very dark green (forest)
            
            bush.setBillboardPointEye()
            bush.setTwoSided(True)  # Visible from both sides
            # Set render order - forest should be above clearing
            bush.setBin("fixed", 20)  # Render after clearing (which is at default 0)
            bush.setDepthTest(False)  # Ensure visibility
            bush.setDepthWrite(False)
            self.bushes.append(bush)
            logger.debug(f"Created forest wall {i} at ({x}, {y}), size ({w}, {h}), texture={forest_texture is not None}, color={bush.getColor() if not forest_texture else 'textured'}")
        
        logger.info(f"Created clearing at center and {len(self.bushes)} bush areas for mode {monkey_mode}")
        logger.info(f"Clearing texture loaded: {clearing_texture is not None}, Forest texture loaded: {forest_texture is not None}")
    
    def _create_road(self, clearing_size_x: float, clearing_size_y: float):
        """Create road strips at clearing edges where monkeys walk. Player cannot step on road."""
        from pathlib import Path
        from panda3d.core import TextureStage, Texture
        
        road_texture = None
        road_path = Path("assets/sprites/minigame/road.png")
        if road_path.exists():
            try:
                road_texture = self.base.loader.loadTexture(str(road_path))
                road_texture.setWrapU(Texture.WMRepeat)
                road_texture.setWrapV(Texture.WMRepeat)
            except Exception as e:
                logger.warning(f"Could not load road sprite: {e}")
        
        half_w = clearing_size_x / 2
        half_h = clearing_size_y / 2
        strips = [
            # Top strip (x along width, z at top)
            (0, half_h - ROAD_WIDTH / 2, clearing_size_x, ROAD_WIDTH),
            # Bottom strip
            (0, -half_h + ROAD_WIDTH / 2, clearing_size_x, ROAD_WIDTH),
            # Left strip (z along height, x at left)
            (-half_w + ROAD_WIDTH / 2, 0, ROAD_WIDTH, clearing_size_y),
            # Right strip
            (half_w - ROAD_WIDTH / 2, 0, ROAD_WIDTH, clearing_size_y),
        ]
        for i, (cx, cy, w, h) in enumerate(strips):
            cm = CardMaker(f"road_{i}")
            cm.setFrame(-w / 2, w / 2, -h / 2, h / 2)
            road = self.base.render.attachNewNode(cm.generate())
            road.setPos(cx, 0.62, cy)  # Just above clearing (0.6)
            if road_texture:
                ts = TextureStage("default")
                road.setTexture(ts, road_texture)
                road.setTexScale(ts, w, h)  # Tile texture (repeat)
            else:
                road.setColor(0.35, 0.3, 0.25, 1.0)  # Brown/gray road
            road.setBillboardPointEye()
            road.setTwoSided(True)
            road.setBin("fixed", 11)
            road.setDepthTest(False)
            road.setDepthWrite(False)
            self.roads.append(road)
        logger.info(f"Created {len(self.roads)} road strips (player cannot step on road)")
    
    def _spawn_group(self, count: int):
        """Spawn a group of monkeys in the forest; they walk out onto the path and along it. count 1–5."""
        distribution = self.balance["monkeys"]["age_distribution"]
        stats_by_age = self.balance["monkeys"]["stats_by_age"]
        edge_offset_x = CLEARING_HALF_W - 0.5
        edge_offset_y = CLEARING_HALF_H - 0.5
        # Spawn inside forest (beyond clearing) so they "come out" onto the path
        forest_offset = 2.5  # units into forest from clearing edge
        
        for _ in range(count):
            rand = random.random()
            cumulative = 0
            age = 1
            for age_str, prob in distribution.items():
                cumulative += prob
                if rand <= cumulative:
                    age = int(age_str)
                    break
            stats = stats_by_age[str(age)]
            
            if self.monkey_mode == "NorthSouth":
                # Walk along top or bottom path; spawn at left or right end IN FOREST
                edge_side = random.choice(["top", "bottom"])
                start_side = random.choice(["left", "right"])
                x = -(CLEARING_HALF_W + forest_offset) if start_side == "left" else (CLEARING_HALF_W + forest_offset)
                y = edge_offset_y if edge_side == "top" else -edge_offset_y
                # Direction: from spawn end toward the other end
                initial_direction = (1, 0) if start_side == "left" else (-1, 0)
                walk_direction = "horizontal"
            else:
                # Walk along left or right path; spawn at top or bottom end IN FOREST
                edge_side = random.choice(["left", "right"])
                start_side = random.choice(["top", "bottom"])
                x = edge_offset_x if edge_side == "right" else -edge_offset_x
                y = (CLEARING_HALF_H + forest_offset) if start_side == "top" else -(CLEARING_HALF_H + forest_offset)
                # Direction: from spawn end toward the other end
                initial_direction = (0, -1) if start_side == "top" else (0, 1)
                walk_direction = "vertical"
            
            monkey = Monkey(
                self.base, age, (x, y), stats, walk_direction, self.monkey_mode,
                base_poop_speed=self._poop_base_speed,
                initial_direction=initial_direction
            )
            self.monkeys.append(monkey)
        
        logger.info(f"Spawned group of {count} monkeys from forest (mode: {self.monkey_mode}, total: {len(self.monkeys)})")
    
    def enter(self, player, monkey_mode: str = "NorthSouth"):
        """Enter minigame
        
        Args:
            player: Player instance
            monkey_mode: "NorthSouth" or "WestEast" - determines where monkeys walk
        """
        super().enter(player)
        
        self.monkey_mode = monkey_mode
        
        # Reset game state
        self.game_time = 0
        self.is_game_over = False
        
        # Player always spawns in center
        player.set_position(0, 0)
        
        # Create clearing, road, and bushes (always same - center clearing)
        self._create_clearing_and_bushes(monkey_mode)
        
        # Spawn: first group (1 monkey); next group only when current group all reached forest
        self._spawn_group_size = 1
        self._cap_5_until_time = None
        self._spawn_group(1)  # First group: one monkey
        
        # Show background (lowest layer)
        if self.background:
            self.background.show()
            logger.info(f"Background shown at position {self.background.getPos()}, hidden={self.background.isHidden()}")
        
        # Show clearing (middle layer - playable area)
        if self.clearing:
            self.clearing.show()
            logger.info(f"Clearing shown at position {self.clearing.getPos()}, hidden={self.clearing.isHidden()}, color={self.clearing.getColor()}")
        
        # Show forest walls (top layer - boundaries)
        for i, bush in enumerate(self.bushes):
            if bush:
                bush.show()
                pos = bush.getPos()
                color = bush.getColor()
                logger.info(f"Forest wall {i} shown at position ({pos.x}, {pos.y}, {pos.z}), hidden={bush.isHidden()}, color={color}")
        
        for road in self.roads:
            if road:
                road.show()
        
        logger.info(f"Minigame visual elements: background={self.background is not None}, clearing={self.clearing is not None}, bushes={len(self.bushes)}, roads={len(self.roads)}")
        
        # Show survival time in HUD
        if hasattr(self.base, 'hud'):
            self.base.hud.show_survival_time()
        
        # Top 10 игроков (без читеров) для этого режима — под статистикой времени
        self.top10_frame = None
        self.top10_labels = []
        self._create_top10_display(monkey_mode)
        
        logger.info(f"Minigame started! Mode: {monkey_mode}")
    
    def update(self, dt: float):
        """Update minigame"""
        if self.is_game_over:
            return
        
        # Update game time
        self.game_time += dt
        
        # Update survival time display
        if hasattr(self.base, 'hud'):
            self.base.hud.update_survival_time(self.game_time)
        
        # Award XP for survival time (continuous)
        if hasattr(self.base, 'progression_system'):
            xp_per_second = self.balance.get("progression", {}).get("xp_per_second_survived", 10)
            xp_gain = xp_per_second * dt
            self.base.progression_system.add_xp(int(xp_gain), "survival")
        
        # Update monkeys and collect new poops
        player_pos = self.base.player.get_position()
        
        monkeys_to_remove = []
        for monkey in self.monkeys:
            result = monkey.update(dt, player_pos)
            if result == "despawn":
                monkeys_to_remove.append(monkey)
                # When a monkey reaches forest, next group size increases (1 → 2 → … → 5)
                self._spawn_group_size = min(self._spawn_group_size + 1, 5)
                if self._spawn_group_size == 5 and self._cap_5_until_time is None:
                    self._cap_5_until_time = self.game_time + 30.0
            elif result:  # It's a poop object
                self.poops.append(result)
        
        for monkey in monkeys_to_remove:
            if monkey in self.monkeys:
                monkey.cleanup()
                self.monkeys.remove(monkey)
        
        # Spawn next group only when current group has all reached the forest (no monkeys left)
        if len(self.monkeys) == 0:
            self._spawn_group(min(self._spawn_group_size, 5))
        
        # Update poops and check collisions
        for poop in self.poops[:]:
            poop.update(dt)
            
            # Check collision with player
            if poop.check_collision(player_pos):
                logger.info("💥 Hit by poop!")
                self.base.health_system.take_damage(1)
                self.poops.remove(poop)
                poop.cleanup()
                
                # Send event to BrainLink for ML training (damage taken)
                self._send_game_event("damage_taken")
                
                # Check game over
                if not self.base.health_system.is_alive():
                    self._game_over()
                    self._send_game_event("player_died")
            
            # Remove dead poops (player dodged!)
            elif not poop.is_alive:
                # Award XP for dodging
                if hasattr(self.base, 'progression_system'):
                    xp_per_dodge = self.balance.get("progression", {}).get("xp_per_dodge", 5)
                    self.base.progression_system.add_xp(xp_per_dodge, "dodge")
                
                # Send event to BrainLink for ML training (successful dodge)
                self._send_game_event("dodge_success")
                
                self.poops.remove(poop)
                poop.cleanup()
    
    def _create_top10_display(self, mode: str):
        """Create Top 10 panel справа, мелкий шрифт (non-cheater runs for this mode)."""
        if not hasattr(self.base, 'save_system') or not self.base.save_system:
            return
        top10 = self.base.save_system.get_top10(mode)
        font = getattr(self.base, 'cyrillic_font', None)
        # Справа, под ML-блоком; мелкий шрифт
        self.top10_frame = DirectFrame(
            frameColor=(0.05, 0.05, 0.1, 0.75),
            frameSize=(0, 0.32, 0, 0.2),
            pos=(0.64, 0, 0.28),
            borderWidth=(0.004, 0.004),
        )
        self.top10_frame.reparentTo(self.base.aspect2d)
        self.top10_frame.setBin("fixed", 50)
        self.top10_title_label = DirectLabel(
            text=t("minigame.top10"),
            text_scale=0.026,
            text_fg=(1, 0.9, 0.3, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0.01, 0, 0.18),
            parent=self.top10_frame,
            text_font=font,
            text_align=TextNode.ALeft,
        )
        for i, (name, t) in enumerate(top10):
            lbl = DirectLabel(
                text=f"{i + 1}. {name[:18]} — {t:.1f}s",
                text_scale=0.02,
                text_fg=(0.85, 0.85, 0.9, 1),
                frameColor=(0, 0, 0, 0),
                pos=(0.01, 0, 0.155 - i * 0.016),
                parent=self.top10_frame,
                text_font=font,
                text_align=TextNode.ALeft,
            )
            self.top10_labels.append(lbl)
        for i in range(len(top10), 10):
            lbl = DirectLabel(
                text="—",
                text_scale=0.018,
                text_fg=(0.5, 0.5, 0.55, 1),
                frameColor=(0, 0, 0, 0),
                pos=(0.01, 0, 0.155 - i * 0.016),
                parent=self.top10_frame,
                text_font=font,
                text_align=TextNode.ALeft,
            )
            self.top10_labels.append(lbl)

    def _game_over(self):
        """Handle game over"""
        self.is_game_over = True
        logger.info(f"🎮 Game Over! Survived: {self.game_time:.1f}s")
        
        # Save best time and stats (time + cheater + username)
        if hasattr(self.base, 'save_system'):
            self.base.save_system.save_minigame_time(self.game_time)
            player_cfg = getattr(self.base, 'game_config', {}).get("player", {})
            username = player_cfg.get("name", "Player")
            cheater = player_cfg.get("cheater_mode", False)
            self.base.save_system.save_minigame_run(self.game_time, cheater, username, getattr(self, "monkey_mode", "NorthSouth"))
        
        # Send event to BrainLink for ML training (game over)
        self._send_game_event("game_over")
        
        # TODO: Show game over screen
    
    def _send_game_event(self, event_name: str):
        """
        Send game event to BrainLink for ML training
        
        When a game event occurs (damage, dodge, etc.), we send the current
        movement event to BrainLink so the ML model can learn which movements
        lead to success or failure.
        
        Args:
            event_name: Event name (e.g., "damage_taken", "dodge_success", "player_died")
        """
        try:
            # Get BrainLink client from input manager
            if not hasattr(self.base, 'input_manager') or not self.base.input_manager.brainlink:
                return
            
            brainlink = self.base.input_manager.brainlink
            
            # Check if ML training is enabled in config
            if not hasattr(self.base, 'game_config'):
                return
            
            bl_config = self.base.game_config.get("brainlink", {})
            if not bl_config.get("send_to_ml", False):
                return
            
            # Send only keyboard-driven movement for ML — never BrainLink prediction (would create feedback loop)
            current_event = self.base.input_manager.get_current_keyboard_event()
            
            if current_event and current_event in ["ml", "mr", "mu", "md"]:
                success = brainlink.send_event_for_ml_training(current_event)
                if success:
                    logger.debug(f"📤 Sent '{event_name}' -> ML training: movement '{current_event}'")
                else:
                    logger.debug(f"⚠️ Failed to send '{event_name}' for ML training")
            else:
                if self.base.input_manager.is_using_brainlink():
                    logger.debug(f"⚠️ Cannot send '{event_name}' for ML: movement from BrainLink (prediction), not sending")
                elif not current_event:
                    logger.debug(f"⚠️ Cannot send '{event_name}' for ML: no keyboard movement event")
        
        except Exception as e:
            logger.warning(f"Error sending game event to BrainLink: {e}", exc_info=True)
    
    def refresh_locale(self):
        if hasattr(self, "top10_title_label") and self.top10_title_label:
            self.top10_title_label["text"] = t("minigame.top10")
    
    def exit(self):
        """Exit minigame"""
        super().exit()
        
        # Hide survival time display
        if hasattr(self.base, 'hud'):
            self.base.hud.hide_survival_time()
        
        # Hide and destroy Top 10 panel
        if getattr(self, 'top10_frame', None):
            self.top10_frame.destroy()
            self.top10_frame = None
        self.top10_labels = []
        
        # Cleanup
        for monkey in self.monkeys:
            monkey.cleanup()
        self.monkeys.clear()
        
        for poop in self.poops:
            poop.cleanup()
        self.poops.clear()
        
        # Hide visual elements
        self.background.hide()
        if self.clearing:
            self.clearing.hide()
        for bush in self.bushes:
            bush.hide()
        for road in self.roads:
            road.hide()
    
    def cleanup(self):
        """Cleanup"""
        super().cleanup()
        
        if self.background:
            self.background.removeNode()
