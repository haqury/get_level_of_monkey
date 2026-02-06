"""Save System - управление сохранениями и статистикой"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class SaveSystem:
    """Система сохранений игры и статистики мини-игр"""
    
    SAVE_FILE = Path("saves/game_save.json")
    STATS_FILE = Path("saves/minigame_stats.json")
    
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
        """Save best minigame survival time (legacy; also record in stats)."""
        save_data = self.load_game() or {}
        current_best = save_data.get("best_time", 0.0)
        if time > current_best:
            save_data["best_time"] = time
            self.save_game(save_data)
            logger.info(f"New best time saved: {time:.1f}s")
        return True

    def save_minigame_run(self, time_seconds: float, cheater: bool, username: str = "", mode: str = "") -> None:
        """
        Save one minigame run to stats: time, cheater, username, mode (NorthSouth / WestEast).
        """
        runs = self._load_stats_runs()
        runs.append({
            "time": round(time_seconds, 1),
            "cheater": bool(cheater),
            "username": username or "Player",
            "mode": mode or "NorthSouth",
            "timestamp": datetime.now().isoformat(),
        })
        self._save_stats_runs(runs)
        logger.info("Minigame run saved: %.1fs, cheater=%s, user=%s, mode=%s", time_seconds, cheater, username or "Player", mode)

    def _load_stats_runs(self) -> list:
        """Load list of minigame runs from stats file."""
        if not self.STATS_FILE.exists():
            return []
        try:
            with open(self.STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("runs", [])
        except Exception as e:
            logger.warning("Could not load minigame stats: %s", e)
            return []

    def _save_stats_runs(self, runs: list) -> None:
        """Save list of minigame runs to stats file."""
        self.SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.STATS_FILE, "w", encoding="utf-8") as f:
                json.dump({"runs": runs}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save minigame stats: %s", e)

    def get_minigame_stats(self, username: Optional[str] = None, mode: Optional[str] = None) -> List[dict]:
        """
        Get minigame stats: list of runs (time, cheater, username, mode).
        If username/mode set, filter.
        """
        runs = self._load_stats_runs()
        if username:
            runs = [r for r in runs if (r.get("username") or "Player") == username]
        if mode:
            runs = [r for r in runs if (r.get("mode") or "NorthSouth") == mode]
        return runs

    def get_leader(self, mode: str) -> tuple:
        """
        Get leader for a minigame mode: best time among non-cheater runs.
        Returns (username, time_seconds) or ("—", 0.0).
        """
        runs = self.get_minigame_stats(mode=mode)
        runs = [r for r in runs if not r.get("cheater", True)]
        if not runs:
            return ("—", 0.0)
        best = max(runs, key=lambda r: r.get("time", 0))
        return (best.get("username") or "Player", best.get("time", 0))

    def get_top10(self, mode: str) -> List[tuple]:
        """
        Get top 10 players for a minigame mode (non-cheater only), sorted by time desc.
        Returns list of (username, time_seconds).
        """
        runs = self.get_minigame_stats(mode=mode)
        runs = [r for r in runs if not r.get("cheater", True)]
        runs.sort(key=lambda r: r.get("time", 0), reverse=True)
        return [(r.get("username") or "Player", r.get("time", 0)) for r in runs[:10]]

    def get_best_time(self) -> float:
        """Get best minigame survival time"""
        save_data = self.load_game()
        if save_data:
            return save_data.get("best_time", 0.0)
        return 0.0
