from game_message import Position, GameMap, AddBiomassAction, RemoveBiomassAction
from path import Path


class Strategy:
    def __init__(self, paths: list[Path]):
        self.paths = paths

        # Priorise les chemins en cours puis les non commencés par efficacité
    def get_priority_paths(self, game_map: GameMap) -> list[Path]:
        in_progress = []
        not_started = []

        # Seuil minimum
        all_values = [p.get_value() for p in self.paths]
        median_value = sorted(all_values)[len(
            all_values) // 2] if all_values else 0
        MIN_VALUE_THRESHOLD = max(2, median_value * 0.3)

        for path in self.paths:
            current_value = path.get_value()
            bottleneck = path.get_bottleneck(game_map)

            if bottleneck < current_value * 0.95:
                if path.is_started(game_map):
                    in_progress.append(path)
                elif current_value >= MIN_VALUE_THRESHOLD:
                    not_started.append(path)

        in_progress.sort(key=lambda p: (p.get_value(
        ) - p.get_bottleneck(game_map)) / max(p.get_value(), 0.1), reverse=True)
        not_started.sort(key=lambda p: p.get_efficiency(), reverse=True)

        return in_progress + not_started

    # Identifie les tuiles nécessitant de la biomasse pour un chemin donné
    def get_tiles_for_path(self, path: Path, game_map: GameMap) -> list[dict]:
        target = int(path.get_value())
        tiles = []

        for pos in path.positions:
            current = game_map.biomass[pos.x][pos.y]
            needed = max(0, target - current)
            if needed > 0:
                tiles.append(
                    {'pos': pos, 'current': current, 'needed': needed})

        tiles.sort(key=lambda t: t['current'])
        return tiles

    def get_excess_tiles(self, game_map: GameMap) -> list[tuple]:
        tile_max_needed = {}

        for path in self.paths:
            if self.should_abandon_path(path, game_map):
                continue

            target = int(path.get_value())
            for pos in path.positions:
                key = (pos.x, pos.y)
                tile_max_needed[key] = max(tile_max_needed.get(key, 0), target)

        removals = []
        for x in range(game_map.width):
            for y in range(game_map.height):
                current = game_map.biomass[x][y]
                if current == 0:
                    continue

                key = (x, y)
                needed = tile_max_needed.get(key, 0)

                if current > needed:
                    excess = current - needed
                    removals.append((Position(x, y), excess))

        removals.sort(key=lambda r: r[1], reverse=True)
        return removals

    # Abandonne un chemin si la valeur est inférieure à un poucentage de la biomasse investie
    def should_abandon_path(self, path: Path, game_map: GameMap) -> bool:
        if not path.is_started(game_map) or path.is_complete(game_map):
            return False

        current_value = path.get_value()
        invested = path.get_current_biomass(game_map)

        # Pourcentage dépendant de la carte
        total_biomass_on_map = sum(sum(row) for row in game_map.biomass)

        if total_biomass_on_map < 15:  # Rythmic Rings
            return current_value < invested * 0.7  # < 70% investi
        else:
            return current_value < invested * 0.5  # Standard


class Actions:
    @staticmethod
    def place(tiles: list[dict], budget: int) -> list[AddBiomassAction]:
        actions = []
        for tile in tiles:
            if budget <= 0:
                break
            amount = min(tile['needed'], budget)
            for _ in range(amount):
                actions.append(AddBiomassAction(
                    position=tile['pos'], amount=1))
            budget -= amount
        return actions

    @staticmethod
    def remove(removals: list[tuple], budget: int) -> list[RemoveBiomassAction]:
        actions = []
        for pos, excess in removals:
            if budget <= 0:
                break
            amount = min(excess, budget, 2)
            for _ in range(amount):
                actions.append(RemoveBiomassAction(position=pos, amount=1))
            budget -= amount
        return actions
