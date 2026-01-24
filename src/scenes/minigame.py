"""Minigame - Monkey Attack"""

import logging
import random
from panda3d.core import CardMaker, Vec3
from src.scenes.base_scene import BaseScene

logger = logging.getLogger(__name__)


class Monkey:
    """Обезьяна в мини-игре"""
    
    def __init__(self, base, age: int, pos: tuple, stats: dict):
        """
        Args:
            base: ShowBase
            age: Возраст обезьяны (1-4)
            pos: Позиция (x, y)
            stats: Характеристики (throw_speed, accuracy, cooldown)
        """
        self.base = base
        self.age = age
        self.position = Vec3(pos[0], 0, pos[1])
        self.stats = stats
        
        # Throwing state
        self.throw_cooldown = 0
        self.max_cooldown = stats["cooldown"]
        
        # Movement state - monkeys run around the field
        self.move_direction = Vec3(
            random.uniform(-1, 1),
            0,
            random.uniform(-1, 1)
        ).normalized()
        self.move_speed = random.uniform(2.0, 5.0)  # Random speed for variety
        self.move_timer = 0.0
        self.move_change_interval = random.uniform(2.0, 5.0)  # Change direction periodically
        
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
        
        return node
    
    def update(self, dt: float, player_pos: tuple):
        """Update monkey - move around and throw poop"""
        # Update movement - monkeys run onto the clearing
        self.move_timer += dt
        if self.move_timer >= self.move_change_interval:
            # Monkeys tend to move toward the clearing (center) or run across it
            distance_from_center = (self.position.x*self.position.x + self.position.z*self.position.z) ** 0.5
            
            if distance_from_center > 20:
                # Far from clearing - run toward it
                if distance_from_center > 0:
                    self.move_direction = Vec3(-self.position.x / distance_from_center, 0, -self.position.z / distance_from_center)
                else:
                    self.move_direction = Vec3(0, 0, -1)
            else:
                # On or near clearing - run around randomly
                self.move_direction = Vec3(
                    random.uniform(-1, 1),
                    0,
                    random.uniform(-1, 1)
                ).normalized()
            
            self.move_timer = 0.0
            self.move_change_interval = random.uniform(1.5, 4.0)
        
        # Move monkey
        movement = self.move_direction * self.move_speed * dt
        new_x = self.position.x + movement.x
        new_y = self.position.z + movement.z
        
        # Keep monkeys on the field (can go on clearing or in bushes)
        distance_from_center = (new_x*new_x + new_y*new_y) ** 0.5
        if distance_from_center > 40:
            # Too far, pull back toward center
            if distance_from_center > 0:
                self.move_direction = Vec3(-new_x / distance_from_center, 0, -new_y / distance_from_center)
            else:
                self.move_direction = Vec3(0, 0, -1)
        
        # Apply movement
        self.position.x += self.move_direction.x * self.move_speed * dt
        self.position.z += self.move_direction.z * self.move_speed * dt
        self.node.setPos(self.position)
        
        # Update throwing cooldown
        self.throw_cooldown -= dt
        
        # Can throw? (cooldown depends on age - older monkeys throw faster)
        if self.throw_cooldown <= 0:
            self.throw_cooldown = self.max_cooldown
            return self._throw_poop(player_pos)
        
        return None
    
    def _throw_poop(self, player_pos: tuple):
        """Throw poop at player"""
        # Calculate direction with accuracy
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
        self.node.setPos(self.position)
        
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
    
    # Start positions (North, South, West, East) - 5x larger
    START_POSITIONS = {
        "North": (0, 15),      # 3 * 5
        "South": (0, -15),     # -3 * 5
        "West": (-15, 0),      # -3 * 5
        "East": (15, 0)        # 3 * 5
    }
    
    # Movement area bounds (relative to field center) - 5x larger
    MOVEMENT_BOUNDS = {
        "min_x": -20.0,  # -4 * 5
        "max_x": 20.0,   # 4 * 5
        "min_y": -20.0,  # -4 * 5
        "max_y": 20.0    # 4 * 5
    }
    
    def __init__(self, base, balance_config: dict):
        super().__init__(base, "Minigame")
        
        self.balance = balance_config["minigame"]
        
        # Game state
        self.monkeys = []
        self.poops = []
        self.game_time = 0
        self.is_game_over = False
        self.selected_start_position = None  # Will be set by dialog
        
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
        """Create minigame background (5x larger)"""
        cm = CardMaker("minigame_bg")
        cm.setFrame(-50, 50, -30, 30)  # 5x larger
        
        self.background = self.base.render.attachNewNode(cm.generate())
        self.background.setPos(0, 1, 0)
        self.background.setColor(0.3, 0.5, 0.2, 1.0)  # Dark green (bushes/forest)
        self.background.setBillboardPointEye()
    
    def _create_clearing_and_bushes(self, start_position: str):
        """Create clearing (поляна) and bushes based on player start position
        
        Args:
            start_position: "North", "South", "West", or "East"
        """
        # Clean up old elements
        if self.clearing:
            self.clearing.removeNode()
        for bush in self.bushes:
            bush.removeNode()
        self.bushes.clear()
        
        # Clearing size (поляна перед персонажем)
        clearing_size_x = 25.0  # Width
        clearing_size_y = 20.0  # Depth
        
        # Determine clearing position based on start position
        # Поляна всегда перед персонажем
        if start_position == "North":
            # Персонаж на севере, поляна вниз (к центру)
            clearing_center = (0, -5)
            # Кусты: сзади (север), слева (запад), справа (восток)
            bush_positions = [
                # Сзади (север)
                (0, 15, 30, 5),  # x, y, width, height
                # Слева (запад)
                (-20, -5, 5, 30),
                # Справа (восток)
                (20, -5, 5, 30),
            ]
        elif start_position == "South":
            # Персонаж на юге, поляна вверх (к центру)
            clearing_center = (0, 5)
            bush_positions = [
                # Сзади (юг)
                (0, -15, 30, 5),
                # Слева (запад)
                (-20, 5, 5, 30),
                # Справа (восток)
                (20, 5, 5, 30),
            ]
        elif start_position == "West":
            # Персонаж на западе, поляна вправо (к центру)
            clearing_center = (5, 0)
            bush_positions = [
                # Сзади (запад)
                (-15, 0, 5, 30),
                # Слева (север)
                (5, 15, 30, 5),
                # Справа (юг)
                (5, -15, 30, 5),
            ]
        else:  # East
            # Персонаж на востоке, поляна влево (к центру)
            clearing_center = (-5, 0)
            bush_positions = [
                # Сзади (восток)
                (15, 0, 5, 30),
                # Слева (север)
                (-5, 15, 30, 5),
                # Справа (юг)
                (-5, -15, 30, 5),
            ]
        
        # Create clearing (поляна) - светлая трава
        cm_clearing = CardMaker("clearing")
        cm_clearing.setFrame(-clearing_size_x/2, clearing_size_x/2, -clearing_size_y/2, clearing_size_y/2)
        self.clearing = self.base.render.attachNewNode(cm_clearing.generate())
        self.clearing.setPos(clearing_center[0], 1.1, clearing_center[1])
        self.clearing.setColor(0.5, 0.7, 0.4, 1.0)  # Light green (clearing)
        self.clearing.setBillboardPointEye()
        
        # Create bushes (кусты) - тёмная зелень
        for x, y, w, h in bush_positions:
            cm_bush = CardMaker(f"bush_{len(self.bushes)}")
            cm_bush.setFrame(-w/2, w/2, -h/2, h/2)
            bush = self.base.render.attachNewNode(cm_bush.generate())
            bush.setPos(x, 1.1, y)
            bush.setColor(0.2, 0.4, 0.15, 1.0)  # Dark green (bushes)
            bush.setBillboardPointEye()
            self.bushes.append(bush)
        
        logger.info(f"Created clearing at {clearing_center} and {len(self.bushes)} bush areas for position {start_position}")
    
    def _spawn_monkeys(self):
        """Spawn monkeys in bushes - they will run onto the clearing"""
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
        
        # Spawn monkeys in bushes (around the clearing, not on it)
        # They will run onto the clearing during gameplay
        spawn_radius = 30  # Outside the clearing
        for i, age in enumerate(ages):
            # Spawn in a circle around the clearing
            angle = (i / count) * 3.14159 * 2
            x = spawn_radius * (angle / 3.14159)
            y = spawn_radius * ((i % 2) * 2 - 1)
            
            # Make sure they're not too close to center (in bushes, not on clearing)
            if abs(x) < 15 and abs(y) < 12:
                # Too close to clearing, push out
                if abs(x) < abs(y):
                    x = 15 if x >= 0 else -15
                else:
                    y = 12 if y >= 0 else -12
            
            stats = stats_by_age[str(age)]
            monkey = Monkey(self.base, age, (x, y), stats)
            self.monkeys.append(monkey)
        
        logger.info(f"Spawned {count} monkeys in bushes (will run onto clearing)")
    
    def enter(self, player, start_position: str = "North"):
        """Enter minigame
        
        Args:
            player: Player instance
            start_position: One of "North", "South", "West", "East"
        """
        super().enter(player)
        
        self.selected_start_position = start_position
        
        # Reset game state
        self.game_time = 0
        self.is_game_over = False
        
        # Set player position based on selection
        if start_position in self.START_POSITIONS:
            pos = self.START_POSITIONS[start_position]
            player.set_position(pos[0], pos[1])
        else:
            # Default to center if invalid
            player.set_position(0, 0)
        
        # Create clearing and bushes based on start position
        self._create_clearing_and_bushes(start_position)
        
        # Spawn monkeys (they will run onto the clearing)
        self._spawn_monkeys()
        
        # Show background
        self.background.show()
        
        # Show clearing and bushes
        if self.clearing:
            self.clearing.show()
        for bush in self.bushes:
            bush.show()
        
        # Show survival time in HUD
        if hasattr(self.base, 'hud'):
            self.base.hud.show_survival_time()
        
        logger.info(f"Minigame started! Position: {start_position}")
    
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
        
        for monkey in self.monkeys:
            new_poop = monkey.update(dt, player_pos)
            if new_poop:
                self.poops.append(new_poop)
        
        # Update poops and check collisions
        for poop in self.poops[:]:
            poop.update(dt)
            
            # Check collision with player
            if poop.check_collision(player_pos):
                logger.info("💥 Hit by poop!")
                self.base.health_system.take_damage(1)
                self.poops.remove(poop)
                poop.cleanup()
                
                # Check game over
                if not self.base.health_system.is_alive():
                    self._game_over()
            
            # Remove dead poops (player dodged!)
            elif not poop.is_alive:
                # Award XP for dodging
                if hasattr(self.base, 'progression_system'):
                    xp_per_dodge = self.balance.get("progression", {}).get("xp_per_dodge", 5)
                    self.base.progression_system.add_xp(xp_per_dodge, "dodge")
                self.poops.remove(poop)
                poop.cleanup()
    
    def _game_over(self):
        """Handle game over"""
        self.is_game_over = True
        logger.info(f"🎮 Game Over! Survived: {self.game_time:.1f}s")
        
        # Save best time
        if hasattr(self.base, 'save_system'):
            self.base.save_system.save_minigame_time(self.game_time)
        
        # TODO: Show game over screen
    
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
