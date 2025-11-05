# Un bot pour enregistrer les valeurs des colonies à chaque tick.
# Écrit les données dans un fichier JSON à la fin de la partie
#
#
# Changer le nom de la carte "hardcodé" ci-dessous avant d'exécuter le bot.

import json
from game_message import TeamGameState
from dataclasses import asdict


class Bot:
    def __init__(self):
        self.colony_history = {}
        self.map_name = 'NOM_DE_LA_CARTE'
        self.first_tick = True

    def get_next_move(self, game_state: TeamGameState):
        if self.first_tick:
            self.first_tick = False

        self._record_tick(game_state)

        if game_state.currentTickNumber >= 350:
            self._save_data()

        return []

    def _record_tick(self, game_state):
        tick = game_state.currentTickNumber

        for colony in game_state.map.colonies:
            col_key = f"{colony.position.x},{colony.position.y}"

            if col_key not in self.colony_history:
                self.colony_history[col_key] = {
                    'position': asdict(colony.position),
                    'nutrient_history': []
                }

            self.colony_history[col_key]['nutrient_history'].append(
                colony.nutrients)

        if tick % 50 == 0:
            print(f"Recorded tick {tick}")

    def _save_data(self):
        colonies = []
        for idx, (col_key, data) in enumerate(sorted(self.colony_history.items())):
            colonies.append({
                'id': idx,
                'position': data['position'],
                'nutrients': data['nutrient_history'][0],
                'futureNutrients': data['nutrient_history']
            })

        output = {'colonies': colonies}
        filename = f"maps/{self.map_name}_colony_data.json"

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nData saved to {filename}")
        print(f"  Colonies: {len(colonies)}")
        print(f"  Ticks: {len(colonies[0]['futureNutrients'])}")
