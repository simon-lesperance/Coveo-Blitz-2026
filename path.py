from game_message import Position, Colony, GameMap


class Path:
    def __init__(self, colony1: Colony, colony2: Colony, positions: list[Position]):
        """Store path between two colonies"""
        self.colony1 = colony1
        self.colony2 = colony2
        self.positions = positions
        self.length = len(positions)

    def get_value(self) -> int:
        """Value of the path"""
        return min(self.colony1.nutrients, self.colony2.nutrients)

    def get_efficiency(self) -> float:
        """Value per biomass unit"""
        return self.get_value() / self.length if self.length > 0 else 0

    def get_current_biomass(self, game_map: GameMap) -> int:
        """Current biomass on the path"""
        total = 0
        for pos in self.positions:
            total += game_map.biomass[pos.x][pos.y]
        return total

    def get_needed_biomass(self, game_map: GameMap) -> int:
        """Biomass needed to reach max capacity"""
        target = self.length * self.get_value()
        current = self.get_current_biomass(game_map)
        return target - current
