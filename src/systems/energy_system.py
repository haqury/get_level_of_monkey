"""Energy System - управление энергией игрока"""

import logging

logger = logging.getLogger(__name__)


class EnergySystem:
    """Система энергии игрока"""
    
    def __init__(self, max_energy: float = 100.0, regen_rate: float = 5.0):
        """
        Args:
            max_energy: Максимальная энергия
            regen_rate: Скорость восстановления (energy/sec)
        """
        self.max_energy = max_energy
        self.current_energy = max_energy
        self.regen_rate = regen_rate
        self.cheater_mode = False  # Cheater mode: unlimited energy
        
        logger.info(f"EnergySystem: max={max_energy}, regen={regen_rate}/sec")
    
    def can_spend(self, amount: float) -> bool:
        """Проверить, можно ли потратить энергию"""
        if self.cheater_mode:
            return True  # Always can spend in cheater mode
        return self.current_energy >= amount
    
    def spend(self, amount: float) -> bool:
        """
        Потратить энергию
        
        Returns:
            True if spent successfully
        """
        if self.cheater_mode:
            return True  # Always succeed in cheater mode, don't reduce energy
        if self.can_spend(amount):
            self.current_energy -= amount
            return True
        return False
    
    def update(self, dt: float):
        """Восстановление энергии"""
        self.current_energy = min(
            self.max_energy,
            self.current_energy + self.regen_rate * dt
        )
    
    def get_percentage(self) -> float:
        """Получить процент энергии (0.0 - 1.0)"""
        return self.current_energy / self.max_energy if self.max_energy > 0 else 0.0
