"""Progression System - система прокачки игрока"""

import logging
import math

logger = logging.getLogger(__name__)


class ProgressionSystem:
    """Система прокачки: опыт, уровни, улучшения"""
    
    def __init__(self, balance_config: dict):
        """
        Args:
            balance_config: Конфигурация прокачки из balance.json
        """
        self.config = balance_config
        
        # Player state
        self.level = 1
        self.current_xp = 0
        self.required_xp = self._calculate_required_xp(1)
        
        # Upgrade levels (сколько раз улучшена каждая характеристика)
        self.upgrade_levels = {
            "max_hp": 0,
            "max_energy": 0,
            "energy_regen": 0,
            "move_speed": 0
        }
        
        # Callbacks
        self.on_level_up = None  # Called when level increases
        self.on_xp_gain = None   # Called when XP is gained
        
        logger.info(f"ProgressionSystem initialized: Level {self.level}, XP {self.current_xp}/{self.required_xp}")
    
    def _calculate_required_xp(self, level: int) -> int:
        """Вычислить требуемый XP для следующего уровня"""
        base = self.config["level_xp_base"]
        # Formula: base * (level ** 1.5)
        return int(base * (level ** 1.5))
    
    def add_xp(self, amount: int, source: str = ""):
        """
        Добавить опыт
        
        Args:
            amount: Количество опыта
            source: Источник опыта (для логирования)
        """
        if amount <= 0:
            return
        
        self.current_xp += amount
        logger.info(f"✨ +{amount} XP ({source}). Total: {self.current_xp}/{self.required_xp}")
        
        if self.on_xp_gain:
            self.on_xp_gain(amount, source)
        
        # Check for level up
        while self.current_xp >= self.required_xp:
            self._level_up()
    
    def _level_up(self):
        """Повысить уровень"""
        self.current_xp -= self.required_xp
        self.level += 1
        self.required_xp = self._calculate_required_xp(self.level)
        
        logger.info(f"🎉 LEVEL UP! New level: {self.level}. Next level needs {self.required_xp} XP")
        
        if self.on_level_up:
            self.on_level_up(self.level)
    
    def get_upgrade_cost(self, upgrade_type: str) -> int:
        """
        Получить стоимость улучшения
        
        Args:
            upgrade_type: Тип улучшения (max_hp, max_energy, energy_regen, move_speed)
        """
        if upgrade_type not in self.upgrade_levels:
            return 0
        
        current_level = self.upgrade_levels[upgrade_type]
        cost_per_level = self.config["upgrades"][upgrade_type]["cost_per_level"]
        # Cost increases with each level (linear)
        return cost_per_level * (current_level + 1)
    
    def can_upgrade(self, upgrade_type: str) -> bool:
        """Проверить, можно ли улучшить характеристику"""
        if upgrade_type not in self.upgrade_levels:
            return False
        
        cost = self.get_upgrade_cost(upgrade_type)
        return self.current_xp >= cost
    
    def upgrade(self, upgrade_type: str) -> bool:
        """
        Улучшить характеристику
        
        Args:
            upgrade_type: Тип улучшения
            
        Returns:
            True если улучшение успешно
        """
        if upgrade_type not in self.upgrade_levels:
            logger.warning(f"Unknown upgrade type: {upgrade_type}")
            return False
        
        if not self.can_upgrade(upgrade_type):
            logger.warning(f"Cannot upgrade {upgrade_type}: not enough XP")
            return False
        
        cost = self.get_upgrade_cost(upgrade_type)
        self.current_xp -= cost
        self.upgrade_levels[upgrade_type] += 1
        
        logger.info(f"🔧 Upgraded {upgrade_type} to level {self.upgrade_levels[upgrade_type]} (cost: {cost} XP)")
        return True
    
    def get_upgrade_value(self, upgrade_type: str) -> float:
        """
        Получить значение улучшения (сколько прибавлено)
        
        Args:
            upgrade_type: Тип улучшения
            
        Returns:
            Общее значение улучшения
        """
        if upgrade_type not in self.upgrade_levels:
            return 0.0
        
        level = self.upgrade_levels[upgrade_type]
        value_per_level = self.config["upgrades"][upgrade_type]["value_per_level"]
        return level * value_per_level
    
    def get_xp_percentage(self) -> float:
        """Получить процент прогресса к следующему уровню (0.0 - 1.0)"""
        if self.required_xp <= 0:
            return 1.0
        return min(1.0, self.current_xp / self.required_xp)
