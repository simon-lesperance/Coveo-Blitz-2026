from game_message import *
from path import Path


class Bot:
    def __init__(self):
        print("Initializing Confidently Wrong Bot!")
        self.all_paths = []
        self.initialized = False

    def get_next_move(self, game_message: TeamGameState):
        print(f"\n--- Turn {game_message.currentTickNumber} ---")

        # Initialize paths on first turn
        if not self.initialized:
            self.initialize_paths(game_message.map)

        ranked_paths = self.rank_paths_by_efficiency()
        actions = self.allocate_biomass(ranked_paths, game_message)
        print(f"Created {len(actions)} actions")
        return actions

    def initialize_paths(self, game_map: GameMap):
        """Calculate all paths between colonies"""
        print("\n=== Initializing Paths ===")
        colonies = game_map.colonies
        pairs = set()

        for i in range(len(colonies)):
            for j in range(i + 1, len(colonies)):
                colony1 = colonies[i]
                colony2 = colonies[j]
                path_positions = self.calculate_path(colony1, colony2)
                path = Path(colony1, colony2, path_positions)
                self.all_paths.append(path)

                print(f"  {path} - Value: {path.get_value()
                                           }, Efficiency: {path.get_efficiency():.2f}")

        print(f"Total paths created: {len(self.all_paths)}\n")
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

        print("\n=== Top 3 Paths by Efficiency ===")
        for i, path in enumerate(sorted_paths[:3]):
            print(f"{i+1}. {path} - Efficiency: {path.get_efficiency():.2f}")

        return sorted_paths

    def allocate_biomass(self, ranked_paths, game_message: TeamGameState):
        """Allocate biomass to paths and create actions"""
        actions = []

        remaining_budget = min(
            game_message.maximumNumberOfBiomassPerTurn,
            game_message.availableBiomass
        )

        print(f"\n=== Allocating Biomass (Budget: {remaining_budget}) ===")

        for path in ranked_paths:
            if remaining_budget <= 0:
                break
            needed = path.get_needed_biomass(game_message.map)
            if needed <= 0:
                continue  # Path already complete
            to_place = min(needed, remaining_budget)

            print(f"  {path}")
            print(f"    Current: {path.get_current_biomass(game_message.map)}, Target: {
                  path.get_value()}, Needed: {needed}, Placing: {to_place}")

            # Create actions to place biomass on this path
            path_actions = self.create_actions_for_path(
                path, to_place, game_message.map)
            actions.extend(path_actions)

            # Update our budget
            remaining_budget -= to_place

        return actions

    def create_actions_for_path(self, path: Path, amount_to_place: int, game_map: GameMap):
        """Create actions to place biomass evenly on path tiles"""
        actions = []

        tiles = [(pos, game_map.biomass[pos.x][pos.y])
                 for pos in path.positions]

        # Sort, emptiest first
        tiles.sort(key=lambda t: t[1])

        remaining = amount_to_place
        tile_index = 0

        while remaining > 0:
            pos, current = tiles[tile_index]
            actions.append(AddBiomassAction(
                position=pos,
                amount=1
            ))

            tiles[tile_index] = (pos, current + 1)
            remaining -= 1

            tile_index = (tile_index + 1) % len(tiles)

            if tile_index == 0:  # Completed a round
                tiles.sort(key=lambda t: t[1])

        return actions
