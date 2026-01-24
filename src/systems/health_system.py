"""Health System - управление здоровьем"""

import logging

logger = logging.getLogger(__name__)


class HealthSystem:
    """Система здоровья игрока"""
    
    def __init__(self, max_hp: int = 3):
        """
        Args:
            max_hp: Максимальное HP
        """
        self.max_hp = max_hp
        self.current_hp = max_hp
        
        # Callbacks
        self.on_damage = None  # Called when damage taken
        self.on_death = None   # Called when HP reaches 0
        
        logger.info(f"HealthSystem: max_hp={max_hp}")
    
    def take_damage(self, amount: int = 1):
        """
        Получить урон
        
        Args:
            amount: Количество урона
        """
        self.current_hp = max(0, self.current_hp - amount)
        logger.info(f"💔 Damage taken! HP: {self.current_hp}/{self.max_hp}")
        
        if self.on_damage:
            self.on_damage(amount)
        
        if self.current_hp <= 0 and self.on_death:
            self.on_death()
    
    def heal(self, amount: int = 1):
        """Восстановить HP"""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        if self.current_hp > old_hp:
            logger.info(f"💚 Healed! HP: {self.current_hp}/{self.max_hp}")
    
    def is_alive(self) -> bool:
        """Проверить, жив ли игрок"""
        return self.current_hp > 0
    
    def get_percentage(self) -> float:
        """Получить процент HP (0.0 - 1.0)"""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
