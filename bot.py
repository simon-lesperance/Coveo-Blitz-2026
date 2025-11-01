from game_message import Position
from game_message import Colony
from game_message import GameMap
from game_message import TeamGameState
from game_message import Action
from game_message import AddBiomassAction
from game_message import RemoveBiomassAction


class Bot:
    def __init__(self):
        print("Initializing Confidently Wrong Bot!")

    def get_next_move(self, game_message: TeamGameState):
        print(f"\n--- Turn {game_message.currentTickNumber} ---")

        sorted_colonies = self.sort_colonies(game_message.map)

        best_colony = sorted_colonies[0]
        nearest_colony = self.get_nearest_colony(
            best_colony, sorted_colonies[1:])

        path = self.calculate_path(
            best_colony, nearest_colony)

        actions = self.place_biomass_on_path(path, game_message)

        return actions

    def available_biomass(self, game_message):
        return min(
            game_message.maximumNumberOfBiomassPerTurn,
            game_message.availableBiomass
        )

    def sort_colonies(self, game_map):
        sorted_colonies = sorted(
            game_map.colonies, key=lambda c: c.nutrients, reverse=True)
        return sorted_colonies

    def get_nearest_colony(self, colony, colonies):
        starting_position = colony.position
        nearest_colony = min(
            colonies,
            key=lambda c: abs(c.position.x - starting_position.x) +
            abs(c.position.y - starting_position.y)
        )
        return nearest_colony

    def calculate_path(self, starting_colony, target_colony):
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

    def place_biomass_on_path(self, path, game_message):
        actions = []
        biomass_to_place = min(
            game_message.maximumNumberOfBiomassPerTurn,
            game_message.availableBiomass
        )

        while biomass_to_place > 0:
            for position in path:
                if biomass_to_place <= 0:
                    break

                action = AddBiomassAction(
                    type="ADD_BIOMASS",
                    position=position,
                    amount=1
                )
                actions.append(action)
                biomass_to_place -= 1

        return actions
