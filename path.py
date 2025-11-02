from game_message import Position, Colony, GameMap

class Path:
    def __init__(self, colony1: Colony, colony2: Colony, positions: list[Position], game_map: GameMap):
        self.colony1 = colony1
        self.colony2 = colony2
        self.positions = [
            p for p in positions if not self._is_colony(p, game_map)]
        self.length = len(self.positions)

    def _is_colony(self, pos: Position, game_map: GameMap) -> bool:
        return any(c.position.x == pos.x and c.position.y == pos.y for c in game_map.colonies)

    # Estime la valeur du chemin en fonction du min des 3 prochains tours
    def get_value(self) -> float:
        future1 = self.colony1.futureNutrients[:3] if self.colony1.futureNutrients else [
        ]
        future2 = self.colony2.futureNutrients[:3] if self.colony2.futureNutrients else [
        ]

        if not future1 or not future2:
            return float(min(self.colony1.nutrients, self.colony2.nutrients))

        min_len = min(len(future1), len(future2))
        future_mins = [min(future1[i], future2[i]) for i in range(min_len)]
        current_min = min(self.colony1.nutrients, self.colony2.nutrients)

        return current_min * 0.6 + (sum(future_mins) / len(future_mins)) * 0.4

        # Estime l'efficacité du chemin (valeur / longueur)
    def get_efficiency(self) -> float:
        if self.length == 0:
            return float('inf')
        return self.get_value() / self.length

    def get_current_biomass(self, game_map: GameMap) -> int:
        return sum(game_map.biomass[p.x][p.y] for p in self.positions)

    def get_bottleneck(self, game_map: GameMap) -> int:
        if not self.positions:
            return int(self.get_value())
        return min(game_map.biomass[p.x][p.y] for p in self.positions)

    def get_completion(self, game_map: GameMap) -> float:
        value = self.get_value()
        if value == 0:
            return 1.0
        return self.get_bottleneck(game_map) / value

    def is_started(self, game_map: GameMap) -> bool:
        return self.get_current_biomass(game_map) > 0

    def is_complete(self, game_map: GameMap) -> bool:
        return self.get_completion(game_map) >= 0.99

    def __repr__(self):
        c1, c2 = self.colony1.position, self.colony2.position
        return f"P({c1.x},{c1.y})-({c2.x},{c2.y})"
