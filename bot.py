from game_message import Position, GameMap, TeamGameState
from path import Path
from strategy import Strategy, Actions


class Bot:
    def __init__(self):
        self.paths = []
        self.all_possible_paths = []
        self.strategy = None
        self.initialized = False
        self.last_reeval_tick = 0

    def get_next_move(self, game_message: TeamGameState):
        if not self.initialized:
            self._initialize(game_message.map)

       # Reevaluate paths every 5 ticks
        if game_message.currentTickNumber - self.last_reeval_tick >= 5:
            self._reevaluate_paths(game_message.map)
            self.last_reeval_tick = game_message.currentTickNumber

        budget = min(game_message.maximumNumberOfBiomassPerTurn,
                     game_message.availableBiomass)
        actions = []

        # Phase 1: Remove excess biomass
        excess = self.strategy.get_excess_tiles(game_message.map)
        if excess:
            removal_budget = min(budget // 2, len(excess))
            removed = Actions.remove(excess, removal_budget)
            actions.extend(removed)
            budget -= len(removed)

        # Phase 2: Build/upgrade priority paths
        priority_paths = self.strategy.get_priority_paths(game_message.map)

        for path in priority_paths:
            if budget <= 0:
                break

            tiles = self.strategy.get_tiles_for_path(path, game_message.map)
            if tiles:
                placed = Actions.place(tiles, budget)
                actions.extend(placed)
                budget -= len(placed)

        # Stats
        completed = sum(
            1 for p in self.paths if p.is_complete(game_message.map))
        in_progress = sum(1 for p in self.paths if p.is_started(game_message.map)
                          and not p.is_complete(game_message.map))

        print(f"T{game_message.currentTickNumber:3d} | Score:{game_message.score:5d} | "
              f"Done:{completed:2d} | InProg:{in_progress:2d} | Budget:{budget}")

        return actions

    def _initialize(self, game_map: GameMap):
        colonies = game_map.colonies

        for i in range(len(colonies)):
            for j in range(i + 1, len(colonies)):
                positions = self._path(
                    colonies[i].position, colonies[j].position)
                path = Path(colonies[i], colonies[j], positions, game_map)
                self.all_possible_paths.append(path)

        # Select initial active paths
        self._reevaluate_paths(game_map)
        self.initialized = True

    def _reevaluate_paths(self, game_map: GameMap):
        self.all_possible_paths.sort(
            key=lambda p: p.get_efficiency(), reverse=True)

        # Limit active paths
        max_paths = min(len(self.all_possible_paths),
                        game_map.width + game_map.height)

        # Keep paths that already have biomass invested
        invested_paths = [p for p in self.all_possible_paths
                          if p.get_current_biomass(game_map) > 0]

        new_paths = []
        for path in self.all_possible_paths:
            if len(invested_paths) + len(new_paths) >= max_paths:
                break
            if path not in invested_paths:
                new_paths.append(path)

        self.paths = invested_paths + new_paths
        self.strategy = Strategy(self.paths)

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
