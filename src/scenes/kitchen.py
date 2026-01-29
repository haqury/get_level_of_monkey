"""Kitchen scene"""

import logging
from panda3d.core import CardMaker
from src.scenes.base_scene import BaseScene
from src.entities.npc import Mother

logger = logging.getLogger(__name__)


class KitchenScene(BaseScene):
    """Кухня"""
    
    def __init__(self, base):
        super().__init__(base, "Kitchen")
        
        # Create background
        self._create_background()
        
        # Create mother NPC (5x position)
        mother = Mother(base, pos=(10, 0))  # 2 * 5
        self.npcs.append(mother)
        
        # Create exit back to cave (5x position)
        self.exits.append({
            "name": "to_cave",
            "pos": (-25, 0),  # -5 * 5
            "target_scene": "cave",
            "text": "← Cave"
        })
        
        # Create exit markers
        self._create_exit_markers()
        
        logger.info("Kitchen scene created")
    
    def _create_background(self):
        """Create kitchen background (5x larger)"""
        cm = CardMaker("kitchen_bg")
        cm.setFrame(-50, 50, -30, 30)  # 5x larger
        
        self.background = self.base.render.attachNewNode(cm.generate())
        self.background.setPos(0, 1, 0)
        self.background.setColor(0.9, 0.9, 0.7, 1.0)  # Light yellow kitchen
        self.background.setBillboardPointEye()
        
        # Create electronic appliances decorations
        self._create_appliances()
    
    def _create_appliances(self):
        """Create electronic appliances decorations with sprites"""
        from pathlib import Path
        
        self.appliances = []
        
        def create_appliance_sprite(name, pos, size):
            """Helper to create appliance with sprite"""
            cm = CardMaker(name)
            cm.setFrame(-size[0], size[0], -size[1], size[1])
            
            node = self.base.render.attachNewNode(cm.generate())
            node.setPos(pos[0], 0, pos[1])
            
            # Try to load sprite
            sprite_path = Path(f"assets/sprites/kitchen/{name}.png")
            if sprite_path.exists():
                try:
                    texture = self.base.loader.loadTexture(str(sprite_path))
                    node.setTexture(texture)
                    node.setTwoSided(True)
                except Exception as e:
                    logger.warning(f"Could not load {name} sprite: {e}")
                    # Fallback to color
                    if name == 'stove':
                        node.setColor(0.5, 0.5, 0.5, 1.0)
                    elif name == 'fridge':
                        node.setColor(0.7, 0.7, 0.9, 1.0)
                    elif name == 'microwave':
                        node.setColor(0.6, 0.6, 0.6, 1.0)
            else:
                # Fallback to color
                if name == 'stove':
                    node.setColor(0.5, 0.5, 0.5, 1.0)
                elif name == 'fridge':
                    node.setColor(0.7, 0.7, 0.9, 1.0)
                elif name == 'microwave':
                    node.setColor(0.6, 0.6, 0.6, 1.0)
            
            node.setBillboardPointEye()
            return node
        
        # Appliances (5x positions)
        # Stove (left side)
        stove_node = create_appliance_sprite("stove", (-20, 10), (0.4, 0.3))  # -4*5, 2*5
        self.appliances.append(stove_node)
        
        # Refrigerator (right side)
        fridge_node = create_appliance_sprite("fridge", (20, 10), (0.3, 0.5))  # 4*5, 2*5
        self.appliances.append(fridge_node)
        
        # Microwave (center-right)
        microwave_node = create_appliance_sprite("microwave", (15, -10), (0.25, 0.2))  # 3*5, -2*5
        self.appliances.append(microwave_node)
        
        # Sink (center-left)
        sink_node = create_appliance_sprite("sink", (-15, -10), (0.3, 0.25))  # -3*5, -2*5
        self.appliances.append(sink_node)
    
    def _create_exit_markers(self):
        """Create exit markers"""
        self.exit_nodes = []
        
        for exit_info in self.exits:
            cm = CardMaker(f"exit_{exit_info['name']}")
            cm.setFrame(-0.8, 0.8, -0.3, 0.3)
            
            node = self.base.render.attachNewNode(cm.generate())
            pos = exit_info["pos"]
            node.setPos(pos[0], 0, pos[1])
            node.setColor(0.2, 1.0, 0.2, 0.7)
            node.setBillboardPointEye()
            
            self.exit_nodes.append(node)
    
    def enter(self, player):
        """Enter kitchen"""
        super().enter(player)
        
        # Set player position (5x)
        player.set_position(-15, 0)  # -3 * 5
        
        # Show background
        self.background.show()
        
        # Show NPCs
        for npc in self.npcs:
            npc.node.show()
        
        # Show exits
        for node in self.exit_nodes:
            node.show()
        
        # Show appliances
        for appliance in self.appliances:
            appliance.show()
    
    def exit(self):
        """Exit kitchen"""
        super().exit()
        
        self.background.hide()
        
        for npc in self.npcs:
            npc.node.hide()
        
        for node in self.exit_nodes:
            node.hide()
        
        # Hide appliances
        for appliance in self.appliances:
            appliance.hide()
    
    def cleanup(self):
        """Cleanup"""
        super().cleanup()
        
        if self.background:
            self.background.removeNode()
        
        for node in self.exit_nodes:
            node.removeNode()
        
        # Cleanup appliances
        for appliance in self.appliances:
            appliance.removeNode()
        self.appliances.clear()