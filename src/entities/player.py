"""Player entity"""

import logging
from pathlib import Path
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CardMaker, Vec3, Vec4, TextureStage, Texture

logger = logging.getLogger(__name__)


class Player(DirectObject):
    """Player character (карапуз)"""
    
    def __init__(self, base, pos=(0, 0)):
        """
        Initialize player
        
        Args:
            base: ShowBase instance
            pos: Initial position (x, y)
        """
        super().__init__()
        
        self.base = base
        self.position = Vec3(pos[0], 0, pos[1])
        
        # Load sprite textures
        self._load_sprites()
        
        # Create visual representation with sprite
        self.node = self._create_visual()
        self.node.reparentTo(base.render)
        # Set Y position to 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
        self.node.setPos(self.position.x, 1.0, self.position.z)
        
        # Animation state
        self.facing_direction = "down"  # up, down, left, right
        self.is_moving = False
        
        logger.info(f"Player created at {pos}")
    
    def _load_sprites(self):
        """Load player sprite textures"""
        sprite_dir = Path("assets/sprites/player")
        self.sprites = {}
        
        try:
            # Load idle sprite
            idle_path = sprite_dir / "idle" / "down.png"
            if idle_path.exists():
                self.sprites['idle'] = self.base.loader.loadTexture(str(idle_path))
            
            # Load walk sprites
            self.sprites['walk'] = {}
            for direction in ['up', 'down', 'left', 'right']:
                walk_path = sprite_dir / "walk" / f"{direction}.png"
                if walk_path.exists():
                    self.sprites['walk'][direction] = self.base.loader.loadTexture(str(walk_path))
            
            logger.info("Player sprites loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load player sprites: {e}, using placeholder")
            self.sprites = {}
    
    def _create_visual(self):
        """Create player visual with sprite"""
        cm = CardMaker("player")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        
        node = self.base.render.attachNewNode(cm.generate())
        
        # Apply sprite texture if available
        if self.sprites:
            if 'idle' in self.sprites:
                node.setTexture(self.sprites['idle'])
            else:
                # Fallback: use default color
                node.setColor(0.2, 0.5, 1.0, 1.0)
        else:
            # Fallback: use default color
            node.setColor(0.2, 0.5, 1.0, 1.0)
        
        node.setBillboardPointEye()
        node.setTwoSided(True)  # Make sprite visible from both sides
        # Set render order - player should be above environment
        node.setBin("fixed", 30)  # Render after environment (background: 0, clearing: 10, forest: 20)
        node.setDepthTest(False)
        node.setDepthWrite(False)
        
        return node
    
    def _update_sprite(self):
        """Update sprite based on movement state and direction"""
        if not self.sprites:
            return
        
        try:
            if self.is_moving and 'walk' in self.sprites:
                if self.facing_direction in self.sprites['walk']:
                    self.node.setTexture(self.sprites['walk'][self.facing_direction])
            elif 'idle' in self.sprites:
                self.node.setTexture(self.sprites['idle'])
        except Exception as e:
            logger.debug(f"Error updating sprite: {e}")
    
    def set_position(self, x: float, y: float):
        """Set player position"""
        self.position = Vec3(x, 0, y)
        # Set Y position to 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
        self.node.setPos(self.position.x, 1.0, self.position.z)
    
    def move(self, dx: float, dy: float, dt: float, speed: float, bounds: dict = None, scene = None):
        """
        Move player with collision checking
        
        Args:
            dx, dy: Direction vector
            dt: Delta time
            speed: Movement speed
            bounds: Optional dict with min_x, max_x, min_y, max_y to constrain movement
            scene: Current scene for collision checking
        """
        if dx != 0 or dy != 0:
            was_moving = self.is_moving
            self.is_moving = True
            
            # Update facing direction
            old_direction = self.facing_direction
            if abs(dx) > abs(dy):
                self.facing_direction = "right" if dx > 0 else "left"
            else:
                self.facing_direction = "up" if dy > 0 else "down"
            
            # Update sprite if direction changed or started moving
            if old_direction != self.facing_direction or not was_moving:
                self._update_sprite()
            
            # Calculate new position
            new_x = self.position.x + dx * speed * dt
            new_y = self.position.z + dy * speed * dt
            
            # Apply bounds if provided
            if bounds:
                new_x = max(bounds.get("min_x", -1000), min(bounds.get("max_x", 1000), new_x))
                new_y = max(bounds.get("min_y", -1000), min(bounds.get("max_y", 1000), new_y))
            
            # Check collisions with scene objects
            if scene and self._check_collision(new_x, new_y, scene):
                # Collision detected, don't move
                return
            
            # Move
            self.position.x = new_x
            self.position.z = new_y
            # Keep Y at 1.0 to be above environment (background: 0.5, clearing: 0.6, forest: 0.7)
            self.node.setPos(self.position.x, 1.0, self.position.z)
        else:
            if self.is_moving:
                self.is_moving = False
                self._update_sprite()  # Switch back to idle
    
    def _check_collision(self, new_x: float, new_y: float, scene) -> bool:
        """
        Check if new position would collide with scene objects
        
        Args:
            new_x, new_y: Proposed new position
            scene: Current scene object
            
        Returns:
            True if collision detected, False otherwise
        """
        player_radius = 0.5  # Player collision radius
        
        # Check collisions with walls (cave boundaries)
        if hasattr(scene, 'wall_nodes') and scene.wall_nodes:
            # Cave boundaries: x = [-35, 35], z = [-18, 18]
            # Walls are at edges: left x=-35, right x=35, top z=18, bottom z=-18
            # Player should stop when touching the wall edge, accounting only for player radius
            # No extra margin - player should be able to get close to walls
            
            # Left wall edge at x = -35
            if new_x < -35 + player_radius:
                return True
            # Right wall edge at x = 35  
            if new_x > 35 - player_radius:
                return True
            # Bottom wall edge at z = -18
            if new_y < -18 + player_radius:
                return True
            # Top wall edge at z = 18
            if new_y > 18 - player_radius:
                return True
        
        # Check collisions with forest/road (minigame) - player cannot step on road or forest
        if hasattr(scene, 'bushes') and scene.bushes and hasattr(scene, 'clearing'):
            # Use scene MOVEMENT_BOUNDS (playable area = clearing minus road)
            if hasattr(scene, 'MOVEMENT_BOUNDS'):
                b = scene.MOVEMENT_BOUNDS
                if new_x < b.get("min_x", -30) + player_radius or new_x > b.get("max_x", 30) - player_radius:
                    return True
                if new_y < b.get("min_y", -15) + player_radius or new_y > b.get("max_y", 15) - player_radius:
                    return True
            else:
                clearing_width = 60.0
                clearing_height = 30.0
                if abs(new_x) > clearing_width/2 - player_radius:
                    return True
                if abs(new_y) > clearing_height/2 - player_radius:
                    return True
        
        # Check collisions with NPCs
        if hasattr(scene, 'npcs'):
            for npc in scene.npcs:
                if hasattr(npc, 'position'):
                    npc_x = npc.position.x if hasattr(npc.position, 'x') else npc.position[0]
                    npc_y = npc.position.z if hasattr(npc.position, 'z') else npc.position[1]
                    dx = new_x - npc_x
                    dy = new_y - npc_y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist < player_radius + 0.6:  # NPC collision radius
                        return True
        
        # Check collisions with blocking objects (appliances, etc)
        if hasattr(scene, 'appliances'):
            for appliance in scene.appliances:
                if appliance and not appliance.isHidden():
                    # Get appliance position
                    pos = appliance.getPos()
                    dx = new_x - pos.x
                    dy = new_y - pos.z
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist < player_radius + 0.8:  # Appliance collision radius
                        return True
        
        return False
    
    def get_position(self):
        """Get player position as (x, y)"""
        return (self.position.x, self.position.z)
    
    def cleanup(self):
        """Cleanup"""
        if self.node:
            self.node.removeNode()
        self.ignoreAll()
