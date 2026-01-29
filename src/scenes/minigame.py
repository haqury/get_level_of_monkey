"""Minigame - Monkey Attack"""

import logging
import random
from panda3d.core import CardMaker, Vec3
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


class Monkey:
    """Обезьяна в мини-игре"""
    
    def __init__(self, base, age: int, pos: tuple, stats: dict, walk_direction: str = "horizontal", monkey_mode: str = "NorthSouth"):
        """
        Args:
            base: ShowBase
            age: Возраст обезьяны (1-4)
            pos: Позиция (x, y)
            stats: Характеристики (throw_speed, accuracy, cooldown)
            walk_direction: "horizontal" or "vertical" - direction along edge
            monkey_mode: "NorthSouth" or "WestEast" - determines movement pattern
        """
        self.base = base
        self.age = age
        self.position = Vec3(pos[0], 0, pos[1])
        self.stats = stats
        self.walk_direction = walk_direction
        self.monkey_mode = monkey_mode
        
        # Throwing state
        self.throw_cooldown = 0
        self.max_cooldown = stats["cooldown"]
        
        # Movement state - monkeys walk along forest edge
        self.move_speed = random.uniform(3.0, 6.0)  # Speed along edge
        
        # Set initial movement direction based on mode
        if monkey_mode == "NorthSouth":
            # Monkeys walk along top/bottom edge (horizontal movement)
            # Random direction: left or right
            direction = random.choice([-1, 1])
            self.move_direction = Vec3(direction, 0, 0)  # Left or Right
        else:  # WestEast
            # Monkeys walk along left/right edge (vertical movement)
            # Random direction: up or down
            direction = random.choice([-1, 1])
            self.move_direction = Vec3(0, 0, direction)  # Up or Down
        
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
                # Set render order - monkeys should be above environment
                node.setBin("fixed", 30)  # Render after environment (background: 0, clearing: 10, forest: 20)
                node.setDepthTest(False)
                node.setDepthWrite(False)
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
        
        return node
    
    def update(self, dt: float, player_pos: tuple):
        """Update monkey - walk along forest edge and throw poop when perpendicular to player"""
        # Move monkey along edge
        movement = self.move_direction * self.move_speed * dt
        new_x = self.position.x + movement.x
        new_y = self.position.z + movement.z
        
        # Keep monkeys on edge - if they reach the end, reverse direction or despawn
        # Use clearing boundaries (playable area) - updated to match new clearing size
        clearing_width = 60.0  # Updated to match new clearing size
        clearing_height = 30.0  # Updated to match new clearing size
        edge_offset_x = clearing_width / 2
        edge_offset_y = clearing_height / 2
        
        if self.monkey_mode == "NorthSouth":
            # Monkeys walk along top/bottom edge (horizontal movement)
            # Keep y position on edge (top or bottom)
            if abs(self.position.z) > edge_offset_y + 1 or abs(self.position.z) < edge_offset_y - 1:
                # Keep on edge - snap to top or bottom edge
                if self.position.z > 0:
                    new_y = edge_offset_y  # Top edge
                else:
                    new_y = -edge_offset_y  # Bottom edge
            
            # Check if reached end of edge
            if new_x > clearing_width/2 or new_x < -clearing_width/2:
                # Reached end - despawn (monkey goes into forest)
                return "despawn"
        else:  # WestEast
            # Monkeys walk along left/right edge (vertical movement)
            # Keep x position on edge (left or right)
            if abs(self.position.x) > edge_offset_x + 1 or abs(self.position.x) < edge_offset_x - 1:
                # Keep on edge - snap to left or right edge
                if self.position.x > 0:
                    new_x = edge_offset_x  # Right edge
                else:
                    new_x = -edge_offset_x  # Left edge
            
            # Check if reached end of edge
            if new_y > clearing_height/2 or new_y < -clearing_height/2:
                # Reached end - despawn
                return "despawn"
        
        # Apply movement
        self.position.x = new_x
        self.position.z = new_y
        # Keep Y at 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
        self.node.setPos(self.position.x, 1.0, self.position.z)
        
        # Check if monkey is perpendicular to player (can throw)
        # Monkey throws when it's directly across from player (perpendicular line)
        can_throw = False
        if self.monkey_mode == "NorthSouth":
            # Monkeys walk along top/bottom edge (horizontal movement along x)
            # Throw when player is at same z level (perpendicular - monkey's x line crosses player's z)
            if abs(self.position.z - player_pos[1]) < 4.0:  # Close enough to be perpendicular
                can_throw = True
        else:  # WestEast
            # Monkeys walk along left/right edge (vertical movement along z)
            # Throw when player is at same x level (perpendicular - monkey's z line crosses player's x)
            if abs(self.position.x - player_pos[0]) < 4.0:  # Close enough to be perpendicular
                can_throw = True
        
        # Update throwing cooldown
        self.throw_cooldown -= dt
        
        # Can throw? Only when perpendicular to player
        if can_throw and self.throw_cooldown <= 0:
            self.throw_cooldown = self.max_cooldown
            return self._throw_poop(player_pos)
        
        return None
    
    def _throw_poop(self, player_pos: tuple):
        """Throw poop at player (perpendicular throw from edge)"""
        # Throw directly at player position with accuracy
        target_x = player_pos[0] + random.uniform(-3, 3) * (1 - self.stats["accuracy"])
        target_y = player_pos[1] + random.uniform(-3, 3) * (1 - self.stats["accuracy"])
        
        return Poop(self.base, self.position.x, self.position.z, target_x, target_y, self.stats["throw_speed"])
    
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
        
        return node
    
    def update(self, dt: float):
        """Update poop position"""
        if not self.is_alive:
            return
        
        # Move
        self.position += self.velocity * dt
        # Keep Y at 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
        self.node.setPos(self.position.x, 1.0, self.position.z)
        
        # Lifetime
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
    
    # Movement area bounds - player restricted to clearing (playable area)
    # Using cave dimensions as base: clearing is 60x30, centered at (0, 0)
    MOVEMENT_BOUNDS = {
        "min_x": -30.0,  # Clearing width / 2 (60.0 / 2)
        "max_x": 30.0,
        "min_y": -15.0,   # Clearing height / 2 (30.0 / 2)
        "max_y": 15.0
    }
    
    def __init__(self, base, balance_config: dict):
        super().__init__(base, "Minigame")
        
        self.balance = balance_config["minigame"]
        
        # Game state
        self.monkeys = []
        self.poops = []
        self.game_time = 0
        self.is_game_over = False
        self.monkey_mode = None  # "NorthSouth" or "WestEast" - determines monkey movement pattern
        
        # Visual elements
        self.clearing = None  # Поляна
        self.bushes = []  # Кусты
        
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
                # Correct tile scale: frame is 70x36 units, sprite is 32x32 pixels
                # Scale to tile properly (divide by sprite size)
                # Correct tile scale: frame is 70x36 units, sprite is 32x32 pixels
                # Match cave scaling: use same approach as cave (35.0, 18.0 for 70x36 frame)
                # This tiles the texture properly across the full area
                self.background.setTexScale(ts, 35.0, 18.0)  # Same as cave for consistency
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
            # Apply tiled texture
            ts = TextureStage('default')
            clearing_texture.setWrapU(Texture.WMRepeat)
            clearing_texture.setWrapV(Texture.WMRepeat)
            self.clearing.setTexture(ts, clearing_texture)
            self.clearing.setTexScale(ts, clearing_size_x / 32.0, clearing_size_y / 32.0)
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
                # Tile texture appropriately
                bush.setTexScale(ts, w / 32.0, h / 32.0)
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
    
    def _spawn_monkeys(self):
        """Spawn monkeys on edges - they will walk along the forest edge"""
        # Clear existing
        for monkey in self.monkeys:
            monkey.cleanup()
        self.monkeys.clear()
        
        # Get config
        count = random.randint(self.balance["monkeys"]["count_min"], self.balance["monkeys"]["count_max"])
        distribution = self.balance["monkeys"]["age_distribution"]
        stats_by_age = self.balance["monkeys"]["stats_by_age"]
        
        # Generate ages based on distribution
        ages = []
        for age_str, prob in distribution.items():
            age = int(age_str)
            num = int(count * prob)
            ages.extend([age] * num)
        
        # Fill to exact count
        while len(ages) < count:
            ages.append(random.choice([1, 2, 3, 4]))
        
        # Spawn monkeys on edges based on mode
        # NorthSouth: monkeys spawn on left/right edges, walk along top/bottom
        # WestEast: monkeys spawn on top/bottom edges, walk along left/right
        # Use clearing boundaries (playable area) - updated to match new clearing size
        clearing_width = 60.0  # Clearing width (updated)
        clearing_height = 30.0  # Clearing height (updated)
        edge_offset_x = clearing_width / 2 - 1  # Slightly inside clearing edge
        edge_offset_y = clearing_height / 2 - 1  # Slightly inside clearing edge
        
        for i, age in enumerate(ages):
            stats = stats_by_age[str(age)]
            
            if self.monkey_mode == "NorthSouth":
                # Monkeys walk along top/bottom edges (horizontal movement)
                # They spawn on left/right edge and walk horizontally
                edge_side = random.choice(["top", "bottom"])
                x = random.uniform(-clearing_width/2, clearing_width/2)  # Random position along edge
                y = edge_offset_y if edge_side == "top" else -edge_offset_y
                walk_direction = "horizontal"
            else:  # WestEast
                # Monkeys walk along left/right edges (vertical movement)
                # They spawn on top/bottom edge and walk vertically
                edge_side = random.choice(["left", "right"])
                x = edge_offset_x if edge_side == "right" else -edge_offset_x
                y = random.uniform(-clearing_height/2, clearing_height/2)  # Random position along edge
                walk_direction = "vertical"
            
            monkey = Monkey(self.base, age, (x, y), stats, walk_direction, self.monkey_mode)
            self.monkeys.append(monkey)
        
        logger.info(f"Spawned {count} monkeys on edges (mode: {self.monkey_mode})")
    
    def _spawn_single_monkey(self):
        """Spawn a single monkey on edge (for continuous spawning)"""
        if len(self.monkeys) >= self.balance["monkeys"]["count_max"]:
            return  # Don't spawn if already at max
        
        distribution = self.balance["monkeys"]["age_distribution"]
        stats_by_age = self.balance["monkeys"]["stats_by_age"]
        
        # Random age based on distribution
        rand = random.random()
        cumulative = 0
        age = 1
        for age_str, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                age = int(age_str)
                break
        
        stats = stats_by_age[str(age)]
        field_size = 25
        edge_offset = 22
        
        # Use clearing boundaries - updated to match new clearing size
        clearing_width = 60.0  # Updated
        clearing_height = 30.0  # Updated
        edge_offset_x = clearing_width / 2 - 1
        edge_offset_y = clearing_height / 2 - 1
        
        if self.monkey_mode == "NorthSouth":
            # Walk along top/bottom edge (horizontal)
            edge_side = random.choice(["top", "bottom"])
            x = random.uniform(-clearing_width/2, clearing_width/2)
            y = edge_offset_y if edge_side == "top" else -edge_offset_y
            walk_direction = "horizontal"
        else:  # WestEast
            # Walk along left/right edge (vertical)
            edge_side = random.choice(["left", "right"])
            x = edge_offset_x if edge_side == "right" else -edge_offset_x
            y = random.uniform(-clearing_height/2, clearing_height/2)
            walk_direction = "vertical"
        
        monkey = Monkey(self.base, age, (x, y), stats, walk_direction, self.monkey_mode)
        self.monkeys.append(monkey)
        logger.debug(f"Spawned new monkey at ({x}, {y})")
    
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
        
        # Create clearing and bushes (always same - center clearing)
        self._create_clearing_and_bushes(monkey_mode)
        
        # Spawn monkeys on edges (they will walk along forest)
        self._spawn_monkeys()
        
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
        
        logger.info(f"Minigame visual elements: background={self.background is not None}, clearing={self.clearing is not None}, bushes={len(self.bushes)}")
        
        # Show survival time in HUD
        if hasattr(self.base, 'hud'):
            self.base.hud.show_survival_time()
        
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
                # Monkey reached end and went into forest
                monkeys_to_remove.append(monkey)
            elif result:  # It's a poop object
                self.poops.append(result)
        
        # Remove despawned monkeys
        for monkey in monkeys_to_remove:
            if monkey in self.monkeys:
                monkey.cleanup()
                self.monkeys.remove(monkey)
        
        # Spawn new monkeys periodically to keep the game challenging
        if random.random() < 0.01 * dt:  # Small chance each frame
            self._spawn_single_monkey()
        
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
    
    def _game_over(self):
        """Handle game over"""
        self.is_game_over = True
        logger.info(f"🎮 Game Over! Survived: {self.game_time:.1f}s")
        
        # Save best time
        if hasattr(self.base, 'save_system'):
            self.base.save_system.save_minigame_time(self.game_time)
        
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
            
            # Get current movement event from BrainLink
            # This is the movement the player was thinking/doing when the game event occurred
            current_event = brainlink.get_event()
            
            if current_event and current_event in ["ml", "mr", "mu", "md"]:
                # Send movement event for ML training
                # The ML model will learn: "When player thought X, game event Y happened"
                success = brainlink.send_event_for_ml_training(current_event)
                if success:
                    logger.debug(f"📤 Sent '{event_name}' -> ML training: movement '{current_event}'")
                else:
                    logger.debug(f"⚠️ Failed to send '{event_name}' for ML training")
            else:
                # If no current movement event, check if player is using keyboard
                # In that case, we can't send ML training data (no EEG data available)
                if not self.base.input_manager.is_using_brainlink():
                    logger.debug(f"⚠️ Cannot send '{event_name}' for ML: player using keyboard (no BrainLink)")
                else:
                    logger.debug(f"⚠️ Cannot send '{event_name}' for ML: no active movement event")
        
        except Exception as e:
            logger.warning(f"Error sending game event to BrainLink: {e}", exc_info=True)
    
    def exit(self):
        """Exit minigame"""
        super().exit()
        
        # Hide survival time display
        if hasattr(self.base, 'hud'):
            self.base.hud.hide_survival_time()
        
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
    
    def cleanup(self):
        """Cleanup"""
        super().cleanup()
        
        if self.background:
            self.background.removeNode()
