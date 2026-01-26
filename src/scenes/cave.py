"""Cave scene - starting location"""

import logging
from panda3d.core import CardMaker, Vec3, TextureStage, Texture
from src.scenes.base_scene import BaseScene
from src.entities.npc import Father

logger = logging.getLogger(__name__)


class CaveScene(BaseScene):
    """Пещера - начальная локация"""
    
    def __init__(self, base):
        super().__init__(base, "Cave")
        
        # Create background
        self._create_background()
        
        # Create father NPC
        father = Father(base, pos=(-10, 10))  # Positioned higher in the room
        self.npcs.append(father)
        
        # Create exits - positioned on walls
        # Right wall at x=35, left wall at x=-35
        # Place exits near walls but slightly inside
        self.exits.append({
            "name": "to_kitchen",
            "pos": (32, 0),  # Right wall - near x=35
            "target_scene": "kitchen",
            "text": "→ Кухня"
        })
        
        self.exits.append({
            "name": "to_outside",
            "pos": (-32, 0),  # Left wall - near x=-35
            "target_scene": "minigame",
            "text": "← Exit (Minigame)"
        })
        
        # Create exit markers
        self._create_exit_markers()
        
        logger.info("Cave scene created")
    
    def _create_background(self):
        """Create cave background with sprites (5x larger)"""
        from pathlib import Path
        
        # Create floor background - sized to fit on screen
        # Frame: left, right, bottom, top
        cm = CardMaker("cave_bg")
        cm.setFrame(-35, 35, -18, 18)  # Reduced vertical size to fit on screen
        
        self.background = self.base.render.attachNewNode(cm.generate())
        self.background.setPos(0, 1, 0)
        
        # Create walls at edges
        self._create_walls()
        
        # Try to load cave floor sprite
        floor_sprite = Path("assets/sprites/cave/cave_floor.png")
        if floor_sprite.exists():
            try:
                texture = self.base.loader.loadTexture(str(floor_sprite))
                # Create a tiled texture by repeating
                texture.setWrapU(Texture.WMRepeat)
                texture.setWrapV(Texture.WMRepeat)
                # Scale texture to tile properly
                ts = TextureStage('default')
                self.background.setTexture(ts, texture)
                self.background.setTexScale(ts, 35.0, 18.0)  # Tile size adjusted
                logger.info("Loaded cave floor sprite")
            except Exception as e:
                logger.warning(f"Could not load cave floor sprite: {e}")
                self.background.setColor(0.3, 0.2, 0.15, 1.0)  # Fallback color
        else:
            self.background.setColor(0.3, 0.2, 0.15, 1.0)  # Fallback color
        
        self.background.setBillboardPointEye()
        self.background.setTwoSided(True)
    
    def _create_walls(self):
        """Create cave walls at edges"""
        from pathlib import Path
        
        self.wall_nodes = []
        wall_sprite = Path("assets/sprites/cave/cave_wall.png")
        wall_texture = None
        
        if wall_sprite.exists():
            try:
                wall_texture = self.base.loader.loadTexture(str(wall_sprite))
                logger.info(f"✓ Loaded cave wall sprite from: {wall_sprite}")
            except Exception as e:
                logger.warning(f"Could not load cave wall sprite: {e}")
        else:
            logger.warning(f"Cave wall sprite not found: {wall_sprite}")
        
        # Create walls at all edges
        wall_height = 18  # Match background height
        wall_width = 35  # Match background width
        wall_thickness = 3.0
        
        # Left wall
        cm_left = CardMaker("cave_wall_left")
        cm_left.setFrame(-wall_thickness, 0, -wall_height, wall_height)
        left_wall = self.base.render.attachNewNode(cm_left.generate())
        left_wall.setPos(-35, 0, 0)  # At left edge
        if wall_texture:
            ts = TextureStage('default')
            left_wall.setTexture(ts, wall_texture)
            # Tile texture vertically
            left_wall.setTexScale(ts, 1.0, wall_height / 32.0)
        else:
            left_wall.setColor(0.25, 0.18, 0.12, 1.0)  # Darker brown
        left_wall.setBillboardPointEye()
        left_wall.setTwoSided(True)
        self.wall_nodes.append(left_wall)
        
        # Right wall
        cm_right = CardMaker("cave_wall_right")
        cm_right.setFrame(0, wall_thickness, -wall_height, wall_height)
        right_wall = self.base.render.attachNewNode(cm_right.generate())
        right_wall.setPos(35, 0, 0)  # At right edge
        if wall_texture:
            ts = TextureStage('default')
            right_wall.setTexture(ts, wall_texture)
            right_wall.setTexScale(ts, 1.0, wall_height / 32.0)
        else:
            right_wall.setColor(0.25, 0.18, 0.12, 1.0)  # Darker brown
        right_wall.setBillboardPointEye()
        right_wall.setTwoSided(True)
        self.wall_nodes.append(right_wall)
        
        # Top wall
        cm_top = CardMaker("cave_wall_top")
        cm_top.setFrame(-wall_width, wall_width, 0, wall_thickness)
        top_wall = self.base.render.attachNewNode(cm_top.generate())
        top_wall.setPos(0, 0, 18)  # At top edge
        if wall_texture:
            ts = TextureStage('default')
            top_wall.setTexture(ts, wall_texture)
            top_wall.setTexScale(ts, wall_width / 32.0, 1.0)
        else:
            top_wall.setColor(0.25, 0.18, 0.12, 1.0)  # Darker brown
        top_wall.setBillboardPointEye()
        top_wall.setTwoSided(True)
        self.wall_nodes.append(top_wall)
        
        # Bottom wall
        cm_bottom = CardMaker("cave_wall_bottom")
        cm_bottom.setFrame(-wall_width, wall_width, -wall_thickness, 0)
        bottom_wall = self.base.render.attachNewNode(cm_bottom.generate())
        bottom_wall.setPos(0, 0, -18)  # At bottom edge
        if wall_texture:
            ts = TextureStage('default')
            bottom_wall.setTexture(ts, wall_texture)
            bottom_wall.setTexScale(ts, wall_width / 32.0, 1.0)
        else:
            bottom_wall.setColor(0.25, 0.18, 0.12, 1.0)  # Darker brown
        bottom_wall.setBillboardPointEye()
        bottom_wall.setTwoSided(True)
        self.wall_nodes.append(bottom_wall)
    
    def _create_exit_markers(self):
        """Create visual markers for exits with sprites"""
        from pathlib import Path
        self.exit_nodes = []
        
        for exit_info in self.exits:
            cm = CardMaker(f"exit_{exit_info['name']}")
            cm.setFrame(-2.0, 2.0, -1.5, 1.5)  # Larger for visibility in 5x scale
            
            node = self.base.render.attachNewNode(cm.generate())
            pos = exit_info["pos"]
            node.setPos(pos[0], 0, pos[1])
            
            # Load appropriate sprite based on exit type
            sprite_path = None
            if exit_info["name"] == "to_outside":
                # Exit to minigame - use cave_exit sprite
                sprite_path = Path("assets/sprites/cave/cave_exit.png")
            elif exit_info["name"] == "to_kitchen":
                # Exit to kitchen - use cave_door sprite
                sprite_path = Path("assets/sprites/cave/cave_door.png")
            
            if sprite_path and sprite_path.exists():
                try:
                    texture = self.base.loader.loadTexture(str(sprite_path))
                    node.setTexture(texture)
                    node.setTwoSided(True)
                    logger.debug(f"Loaded exit sprite: {sprite_path}")
                except Exception as e:
                    logger.warning(f"Could not load exit sprite: {e}")
                    node.setColor(0.2, 1.0, 0.2, 0.7)  # Fallback green
            else:
                node.setColor(0.2, 1.0, 0.2, 0.7)  # Fallback green
            
            node.setBillboardPointEye()
            self.exit_nodes.append(node)
    
    def enter(self, player):
        """Enter cave"""
        super().enter(player)
        
        # Set player position
        player.set_position(-3, 0)  # Adjusted for smaller room
        
        # Show background
        if hasattr(self, 'background') and self.background:
            self.background.show()
        
        # Show walls
        if hasattr(self, 'wall_nodes'):
            for wall in self.wall_nodes:
                if wall:
                    wall.show()
        
        # Show NPCs
        for npc in self.npcs:
            if hasattr(npc, 'node') and npc.node:
                npc.node.show()
        
        # Show exits
        if hasattr(self, 'exit_nodes'):
            for node in self.exit_nodes:
                if node:
                    node.show()
        
        # Ensure player node is visible and parented
        if hasattr(player, 'node') and player.node:
            player.node.show()
            if not player.node.getParent():
                player.node.reparentTo(self.base.render)
        
        # Ensure all elements are properly parented to render tree
        if hasattr(self, 'background') and self.background:
            if not self.background.getParent():
                self.background.reparentTo(self.base.render)
        
        # Force render update to ensure visibility (multiple passes)
        try:
            # Flatten render tree for better rendering
            self.base.render.flattenStrong()
            # Then force multiple render passes
            for _ in range(5):
                self.base.graphicsEngine.renderFrame()
                self.base.graphicsEngine.syncFrame()
        except Exception as e:
            logger.warning(f"Error forcing render in cave enter: {e}")
    
    def exit(self):
        """Exit cave"""
        super().exit()
        
        # Hide everything
        self.background.hide()
        
        for wall in self.wall_nodes:
            wall.hide()
        
        for npc in self.npcs:
            npc.node.hide()
        
        for node in self.exit_nodes:
            node.hide()
    
    def cleanup(self):
        """Cleanup"""
        super().cleanup()
        
        if self.background:
            self.background.removeNode()
        
        for wall in self.wall_nodes:
            wall.removeNode()
        
        for node in self.exit_nodes:
            node.removeNode()
