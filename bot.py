from game_message import Position, GameMap, TeamGameState
from path import Path
from strategy import Strategy, Actions


class Bot:
    def __init__(self):
        self.paths = []
        self.strategy = None
        self.initialized = False

    def get_next_move(self, game_message: TeamGameState):
        if not self.initialized:
            self._initialize(game_message.map)

        budget = min(game_message.maximumNumberOfBiomassPerTurn,
                     game_message.availableBiomass)
        actions = []

        # Enlève l'excès de biomasse
        excess = self.strategy.get_excess_tiles(game_message.map)
        if excess:
            removed = Actions.remove(excess, min(budget // 4, 3))
            actions.extend(removed)
            budget -= len(removed)

        # Priorise les chemins en cours puis les non commencés par efficacité
        priority_paths = self.strategy.get_priority_paths(game_message.map)
        if priority_paths and budget > 0:
            tiles = self.strategy.get_tiles_for_path(
                priority_paths[0], game_message.map)
            if tiles:
                actions.extend(Actions.place(tiles, budget))

        completed = sum(
            1 for p in self.paths if p.is_complete(game_message.map))
        in_progress = sum(1 for p in self.paths if p.is_started(
            game_message.map) and not p.is_complete(game_message.map))
        print(f"T{game_message.currentTickNumber:3d} | Score:{
              game_message.score:5d} | Done:{completed:2d} | InProg:{in_progress:2d}")

        return actions

    def _initialize(self, game_map: GameMap):
        colonies = game_map.colonies
        for i in range(len(colonies)):
            for j in range(i + 1, len(colonies)):
                positions = self._path(
                    colonies[i].position, colonies[j].position)
                self.paths.append(
                    Path(colonies[i], colonies[j], positions, game_map))
        self.strategy = Strategy(self.paths)
        self.initialized = True

    def _path(self, start: Position, end: Position) -> list[Position]:
        path = []
        x, y = start.x, start.y
        while x != end.x or y != end.y:
            if x < end.x:
                x += 1
            elif x > end.x:
                x -= 1
            elif y < end.y:
                y += 1
            elif y > end.y:
                y -= 1
            if x != end.x or y != end.y:
                path.append(Position(x, y))
        return path
