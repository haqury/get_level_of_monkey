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
        field_size = 25
        edge_offset = 22
        
        if self.monkey_mode == "NorthSouth":
            # Monkeys walk along top/bottom edge (horizontal movement)
            # Keep y position on edge (top or bottom)
            if abs(self.position.z) > edge_offset + 2 or abs(self.position.z) < edge_offset - 2:
                # Keep on edge - snap to top or bottom edge
                if self.position.z > 0:
                    new_y = edge_offset  # Top edge
                else:
                    new_y = -edge_offset  # Bottom edge
            
            # Check if reached end of edge
            if new_x > field_size or new_x < -field_size:
                # Reached end - despawn (monkey goes into forest)
                return "despawn"
        else:  # WestEast
            # Monkeys walk along left/right edge (vertical movement)
            # Keep x position on edge (left or right)
            if abs(self.position.x) > edge_offset + 2 or abs(self.position.x) < edge_offset - 2:
                # Keep on edge - snap to left or right edge
                if self.position.x > 0:
                    new_x = edge_offset  # Right edge
                else:
                    new_x = -edge_offset  # Left edge
            
            # Check if reached end of edge
            if new_y > field_size or new_y < -field_size:
                # Reached end - despawn
                return "despawn"
        
        # Apply movement
        self.position.x = new_x
        self.position.z = new_y
        self.node.setPos(self.position)
        
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
    
    # Monkey movement modes (determines where monkeys walk)
    # NorthSouth: monkeys walk from left and right edges (along top/bottom)
    # WestEast: monkeys walk from top and bottom edges (along left/right)
    
    # Movement area bounds - player can move freely (no restrictions)
    MOVEMENT_BOUNDS = None  # No bounds - full freedom
    
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
        """Create minigame background (5x larger)"""
        cm = CardMaker("minigame_bg")
        cm.setFrame(-50, 50, -30, 30)  # 5x larger
        
        self.background = self.base.render.attachNewNode(cm.generate())
        self.background.setPos(0, 1, 0)
        self.background.setColor(0.3, 0.5, 0.2, 1.0)  # Dark green (bushes/forest)
        self.background.setBillboardPointEye()
    
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
        
        # Clearing size - large clearing in center
        clearing_size_x = 30.0  # Width
        clearing_size_y = 30.0  # Depth
        
        # Clearing always in center (player spawns here)
        clearing_center = (0, 0)
        
        # Create bushes around edges (forest)
        # Top edge
        bush_positions = [
            # Top (север)
            (0, 20, 50, 5),  # x, y, width, height
            # Bottom (юг)
            (0, -20, 50, 5),
            # Left (запад)
            (-25, 0, 5, 40),
            # Right (восток)
            (25, 0, 5, 40),
        ]
        
        # Create clearing (поляна) - светлая трава в центре
        cm_clearing = CardMaker("clearing")
        cm_clearing.setFrame(-clearing_size_x/2, clearing_size_x/2, -clearing_size_y/2, clearing_size_y/2)
        self.clearing = self.base.render.attachNewNode(cm_clearing.generate())
        self.clearing.setPos(clearing_center[0], 1.1, clearing_center[1])
        self.clearing.setColor(0.5, 0.7, 0.4, 1.0)  # Light green (clearing)
        self.clearing.setBillboardPointEye()
        
        # Create bushes (кусты) - тёмная зелень по краям
        for x, y, w, h in bush_positions:
            cm_bush = CardMaker(f"bush_{len(self.bushes)}")
            cm_bush.setFrame(-w/2, w/2, -h/2, h/2)
            bush = self.base.render.attachNewNode(cm_bush.generate())
            bush.setPos(x, 1.1, y)
            bush.setColor(0.2, 0.4, 0.15, 1.0)  # Dark green (bushes/forest)
            bush.setBillboardPointEye()
            self.bushes.append(bush)
        
        logger.info(f"Created clearing at center and {len(self.bushes)} bush areas for mode {monkey_mode}")
    
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
        field_size = 25  # Edge of field
        edge_offset = 22  # Slightly inside edge
        
        for i, age in enumerate(ages):
            stats = stats_by_age[str(age)]
            
            if self.monkey_mode == "NorthSouth":
                # Monkeys walk along top/bottom edges (horizontal movement)
                # They spawn on left/right edge and walk horizontally
                edge_side = random.choice(["top", "bottom"])
                x = random.uniform(-field_size, field_size)  # Random position along edge
                y = edge_offset if edge_side == "top" else -edge_offset
                walk_direction = "horizontal"
            else:  # WestEast
                # Monkeys walk along left/right edges (vertical movement)
                # They spawn on top/bottom edge and walk vertically
                edge_side = random.choice(["left", "right"])
                x = edge_offset if edge_side == "right" else -edge_offset
                y = random.uniform(-field_size, field_size)  # Random position along edge
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
        
        if self.monkey_mode == "NorthSouth":
            # Walk along top/bottom edge (horizontal)
            edge_side = random.choice(["top", "bottom"])
            x = random.uniform(-field_size, field_size)
            y = edge_offset if edge_side == "top" else -edge_offset
            walk_direction = "horizontal"
        else:  # WestEast
            # Walk along left/right edge (vertical)
            edge_side = random.choice(["left", "right"])
            x = edge_offset if edge_side == "right" else -edge_offset
            y = random.uniform(-field_size, field_size)
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
