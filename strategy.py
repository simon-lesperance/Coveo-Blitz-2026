from game_message import Position, GameMap, AddBiomassAction, RemoveBiomassAction
from path import Path


class Strategy:
    def __init__(self, paths: list[Path]):
        self.paths = paths

        # Priorise les chemins en cours puis les non commencés par efficacité
    def get_priority_paths(self, game_map: GameMap) -> list[Path]:
        in_progress = []
        not_started = []

        for path in self.paths:
            if path.is_complete(game_map):
                continue
            elif path.is_started(game_map):
                in_progress.append(path)
            else:
                not_started.append(path)

        in_progress.sort(key=lambda p: p.get_completion(
            game_map), reverse=True)
        not_started.sort(key=lambda p: (
            p.get_efficiency(), -p.length), reverse=True)

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

    # Identifie les tuiles avec un excès de biomasse
    def get_excess_tiles(self, game_map: GameMap) -> list[tuple]:
        tile_max_needed = {}

        for path in self.paths:
            if path.is_complete(game_map):
                continue
            target = int(path.get_value())
            for pos in path.positions:
                key = (pos.x, pos.y)
                if key not in tile_max_needed:
                    tile_max_needed[key] = target
                else:
                    tile_max_needed[key] = max(tile_max_needed[key], target)

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
