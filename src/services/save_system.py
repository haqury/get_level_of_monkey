"""Save System - управление сохранениями"""

import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SaveSystem:
    """Система сохранений игры"""
    
    SAVE_FILE = Path("saves/game_save.json")
    
    def __init__(self):
        """Initialize save system"""
        self.SAVE_FILE.parent.mkdir(exist_ok=True)
        logger.info("SaveSystem initialized")
    
    def save_game(self, game_data: dict):
        """
        Save game data
        
        Args:
            game_data: Dict with game state
                - level: int
                - current_xp: int
                - upgrade_levels: dict
                - current_scene: str
                - best_time: float (minigame best survival time)
        """
        try:
            save_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "game": game_data
            }
            
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Game saved to {self.SAVE_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return False
    
    def load_game(self) -> dict:
        """
        Load game data
        
        Returns:
            Dict with game state or None if no save exists
        """
        if not self.SAVE_FILE.exists():
            logger.info("No save file found")
            return None
        
        try:
            with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            logger.info(f"Game loaded from {self.SAVE_FILE}")
            return save_data.get("game", None)
        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return None
    
    def save_minigame_time(self, time: float):
        """Save best minigame survival time"""
        save_data = self.load_game() or {}
        
        current_best = save_data.get("best_time", 0.0)
        if time > current_best:
            save_data["best_time"] = time
            self.save_game(save_data)
            logger.info(f"New best time saved: {time:.1f}s")
            return True
        return False
    
    def get_best_time(self) -> float:
        """Get best minigame survival time"""
        save_data = self.load_game()
        if save_data:
            return save_data.get("best_time", 0.0)
        return 0.0
