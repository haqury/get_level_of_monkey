"""Scene Manager - управление сценами/локациями"""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SceneManager:
    """Менеджер сцен с ленивой загрузкой"""
    
    def __init__(self, base):
        """
        Initialize scene manager
        
        Args:
            base: ShowBase instance
        """
        self.base = base
        self.scene_factories = {}  # {scene_id: factory_function} - функции создания сцен
        self.loaded_scenes = {}    # {scene_id: scene_object} - загруженные сцены
        self.current_scene = None
        self.current_scene_id = None
        
        logger.info("SceneManager initialized (lazy loading enabled)")
    
    def register_scene_factory(self, scene_id: str, factory: Callable):
        """
        Register scene factory function (lazy loading)
        
        Args:
            scene_id: Scene identifier
            factory: Function that creates and returns scene object
                    Called as: factory(base, *args, **kwargs)
        """
        self.scene_factories[scene_id] = factory
        logger.info(f"Scene factory '{scene_id}' registered")
    
    def add_scene(self, scene_id: str, scene):
        """
        Add scene directly (for immediate loading, e.g. main menu)
        
        Args:
            scene_id: Scene identifier
            scene: Scene object
        """
        self.loaded_scenes[scene_id] = scene
        logger.info(f"Scene '{scene_id}' loaded immediately")
    
    def switch_to(self, scene_id: str, player, *args, **kwargs):
        """
        Switch to scene (lazy loading)
        
        Args:
            scene_id: Target scene ID
            player: Player object
            *args, **kwargs: Additional arguments passed to scene factory and scene.enter()
        """
        # Auto-save before switching scenes
        if hasattr(self.base, 'save_system') and self.current_scene:
            self._auto_save()
        
        # Exit current scene
        if self.current_scene:
            self.current_scene.exit()
            # Unload previous scene to free memory (except main_menu which stays loaded)
            if self.current_scene_id != "main_menu" and self.current_scene_id in self.loaded_scenes:
                self.current_scene.cleanup()
                del self.loaded_scenes[self.current_scene_id]
                logger.info(f"Unloaded scene: {self.current_scene_id}")
        
        # Load scene if not loaded (lazy loading)
        if scene_id not in self.loaded_scenes:
            if scene_id in self.scene_factories:
                logger.info(f"Loading scene: {scene_id} (lazy load)")
                scene = self.scene_factories[scene_id](self.base, *args, **kwargs)
                self.loaded_scenes[scene_id] = scene
            elif scene_id in self.loaded_scenes:
                scene = self.loaded_scenes[scene_id]
            else:
                logger.error(f"Scene '{scene_id}' not found! Available: {list(self.scene_factories.keys()) + list(self.loaded_scenes.keys())}")
                return
        else:
            scene = self.loaded_scenes[scene_id]
        
        # Enter new scene
        self.current_scene = scene
        self.current_scene_id = scene_id
        self.current_scene.enter(player, *args, **kwargs)
        
        # Force multiple render updates to ensure scene is visible (fixes gray screen issue)
        try:
            # Multiple passes to ensure everything renders
            for _ in range(5):
                self.base.graphicsEngine.renderFrame()
                self.base.graphicsEngine.syncFrame()
            logger.debug(f"Forced render after entering scene: {scene_id}")
        except Exception as e:
            logger.warning(f"Error forcing render: {e}")
        
        logger.info(f"Switched to scene: {scene_id}")
    
    def _auto_save(self):
        """Auto-save game state"""
        if not hasattr(self.base, 'save_system') or not hasattr(self.base, 'progression_system'):
            return
        
        try:
            save_data = {
                "level": self.base.progression_system.level,
                "current_xp": self.base.progression_system.current_xp,
                "upgrade_levels": self.base.progression_system.upgrade_levels.copy(),
                "current_scene": self.get_current_scene_name() or "cave"
            }
            self.base.save_system.save_game(save_data)
        except Exception as e:
            logger.warning(f"Auto-save failed: {e}")
    
    def get_current_scene(self):
        """Get current active scene"""
        return self.current_scene
    
    def get_current_scene_name(self):
        """Get current scene ID"""
        return self.current_scene_id
    
    def update(self, dt: float):
        """Update current scene"""
        if self.current_scene:
            self.current_scene.update(dt)
    
    def cleanup(self):
        """Cleanup all loaded scenes"""
        for scene_id, scene in self.loaded_scenes.items():
            scene.cleanup()
        self.loaded_scenes.clear()
        self.scene_factories.clear()
