from game_message import Position
from game_message import GameMap
from game_message import TeamGameState
from game_message import AddBiomassAction
from path import Path


class Bot:
    def __init__(self):
        print("Initializing Confidently Wrong Bot!")
        self.all_paths = []
        self.initialized = False

    def get_next_move(self, game_message: TeamGameState):
        print(f"\n--- Turn {game_message.currentTickNumber} ---")

        # Initialize paths
        if not self.initialized:
            self.initialize_paths(game_message.map)

        ranked_paths = self.rank_paths_by_efficiency()
        actions = self.allocate_biomass(ranked_paths, game_message)
        print(f"Created {len(actions)} actions")
        return actions

    def initialize_paths(self, game_map: GameMap):
        """Calculate all paths from colony to colony"""
        colonies = game_map.colonies
        for i in range(len(colonies)):
            for j in range(i + 1, len(colonies)):
                colony1 = colonies[i]
                colony2 = colonies[j]
                path_positions = self.calculate_path(colony1, colony2)
                path = Path(colony1, colony2, path_positions, game_map)
                self.all_paths.append(path)
        self.initialized = True

    def calculate_path(self, starting_colony, target_colony):
        """Calculate a path between two colonies"""
        path = []
        current = starting_colony.position
        target = target_colony.position
        while current != target:
            if current.x < target.x:
                current = Position(current.x + 1, current.y)
            elif current.x > target.x:
                current = Position(current.x - 1, current.y)
            elif current.y < target.y:
                current = Position(current.x, current.y + 1)
            elif current.y > target.y:
                current = Position(current.x, current.y - 1)
            if current != target:
                path.append(current)
        return path

    def rank_paths_by_efficiency(self):
        """Sort paths by efficiency (value per biomass)"""
        sorted_paths = sorted(
            self.all_paths,
            key=lambda p: p.get_efficiency(),
            reverse=True
        )
        return sorted_paths

    def allocate_biomass(self, ranked_paths, game_message: TeamGameState):
        """Allocate biomass to paths and create actions"""
        actions = []
        remaining_budget = min(
            game_message.maximumNumberOfBiomassPerTurn,
            game_message.availableBiomass
        )
        for path in ranked_paths:
            if remaining_budget <= 0:
                break
            needed = path.get_needed_biomass(game_message.map)
            if needed <= 0:
                continue  # Path already complete
            to_place = min(needed, remaining_budget)

            # Create actions
            path_actions = self.create_actions_for_path(
                path, to_place, game_message.map)
            actions.extend(path_actions)

            # Update budget
            remaining_budget -= to_place

        return actions

    def create_actions_for_path(self, path: Path, amount_to_place: int, game_map: GameMap):
        """Create actions to place biomass evenly on path"""
        actions = []
        if len(path.biomass_positions) == 0:
            return actions
        tiles = []
        for pos in path.biomass_positions:
            current_biomass = game_map.biomass[pos.x][pos.y]
            tiles.append((pos, current_biomass))
        # Sort by current biomass (Start with least filled)
        tiles.sort(key=lambda t: t[1])
        remaining = amount_to_place
        index = 0
        while remaining > 0:
            pos, current_biomass = tiles[index]
            actions.append(AddBiomassAction(
                position=pos,
                amount=1
            ))
            tiles[index] = (pos, current_biomass + 1)
            remaining -= 1
            index = (index + 1) % len(tiles)
            # Trier à chaque boucle
            if (index == 0):
                tiles.sort(key=lambda t: t[1])
        return actions
