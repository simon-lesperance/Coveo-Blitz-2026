from game_message import Position, Colony, GameMap


class Path:
    def __init__(self, colony1: Colony, colony2: Colony, positions: list[Position], game_map: GameMap):
        """Store path between two colonies"""
        self.colony1 = colony1
        self.colony2 = colony2
        self.positions = positions
        self.biomass_positions = [
            pos for pos in positions
            if not self.is_colony_position(pos, game_map)
        ]
        self.length = len(self.biomass_positions)

    def is_colony_position(self, pos: Position, game_map: GameMap) -> bool:
        """Check if is a colony position"""
        for colony in game_map.colonies:
            if colony.position.x == pos.x and colony.position.y == pos.y:
                return True
        return False

    def get_value(self) -> int:
        """Value of the path"""
        return min(self.colony1.nutrients, self.colony2.nutrients)

    def get_efficiency(self) -> float:
        """Value per biomass needed"""
        if self.length == 0:
            return float('inf')
        return self.get_value() / self.length

    def get_current_biomass(self, game_map: GameMap) -> int:
        """Current biomass on the path"""
        total = 0
        for pos in self.biomass_positions:
            total += game_map.biomass[pos.x][pos.y]
        return total

    def get_needed_biomass(self, game_map: GameMap) -> int:
        """Biomass needed to reach max capacity"""
        target = self.length * self.get_value()
        current = self.get_current_biomass(game_map)
        return target - current
