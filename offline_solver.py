from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, value
from game_message import Position, GameMap, Colony, AddBiomassAction, RemoveBiomassAction
from path import Path
import json
import math


class OfflineSolver:
    """Calcule les actions optimales pour une carte"""

    def __init__(self, map_config):
        self.map_config = map_config
        self.total_ticks = 351  # Observé sur le site
        self.paths = []

    def solve_full_game(self, time_limit_per_chunk=300):
        # Résout l'ensemble du jeu en chunks.
        print(f"\n{'='*60}")
        print(f"Solving {self.map_config['name']} ({
              self.map_config['difficulty']})")
        print(f"{'='*60}")

        # Generate all paths
        self.paths = self._generate_paths()
        print(f"Generated {len(self.paths)} paths between colonies")

        # Chunks plus petits (30) => plus rapide mais moins optimal
        # Chunks plus gros (100) => plus lent mais plus optimal
        chunk_size = 50
        all_actions = {}
        current_biomass = [[0] * self.map_config['height']
                           for _ in range(self.map_config['width'])]

        for start_tick in range(0, self.total_ticks, chunk_size):
            end_tick = min(start_tick + chunk_size, self.total_ticks)
            print(f"\nSolving ticks {start_tick}-{end_tick}...")

            chunk_actions = self._solve_chunk(
                start_tick,
                end_tick,
                current_biomass,
                time_limit_per_chunk
            )

            if chunk_actions is None:
                print(f"Failed to solve chunk {start_tick}-{end_tick}")
                return None

            # Update etat et enregistre actions
            for tick, actions in chunk_actions.items():
                all_actions[tick] = actions
                # Apply actions to current_biomass
                for action in actions:
                    x, y = action['position']['x'], action['position']['y']
                    if action['type'] == 'ADD_BIOMASS':
                        current_biomass[x][y] += action['amount']
                    else:
                        current_biomass[x][y] -= action['amount']

            print(f"  ✓ Chunk solved, {len(chunk_actions)} ticks planned")

        solution = {
            'map_name': self.map_config['name'],
            'total_ticks': self.total_ticks,
            'actions': all_actions
        }

        return solution

    def _solve_chunk(self, start_tick, end_tick, initial_biomass, time_limit):
        """Solve a chunk of ticks"""
        horizon = end_tick - start_tick
        model = LpProblem(f"Mycelium_{start_tick}_{end_tick}", LpMaximize)

        # Variables
        # Biomasse (Position x, y, tick t)
        biomass = {}
        for t in range(horizon):
            for x in range(self.map_config['width']):
                for y in range(self.map_config['height']):
                    biomass[x, y, t] = LpVariable(
                        f"b_{x}_{y}_{t}",
                        lowBound=0,
                        upBound=100,
                        cat='Integer'
                    )

        # Flow (Path i, tick t)
        flow = {}
        for i in range(len(self.paths)):
            for t in range(horizon):
                flow[i, t] = LpVariable(f"f_{i}_{t}", lowBound=0)

        # Objectif: Maximiser le score total sur tous les ticks/paths
        # Score = Sum(Flow * min(colony values))
        score_terms = []
        for t in range(horizon):
            actual_tick = start_tick + t
            for i, path in enumerate(self.paths):
                colony_value = self._predict_colony_value(path, actual_tick)
                score_terms.append(flow[i, t] * colony_value)

        model += lpSum(score_terms)

        # Contrainte:
        # La biomasse doit être sur un chemin
        for t in range(horizon):
            for i, path in enumerate(self.paths):
                for pos in path.positions:
                    model += flow[i, t] <= biomass[pos.x, pos.y, t]

        # Constrainte:
        # Budget maximal par tour (ajouts + retraits)
        for t in range(horizon):
            additions = []
            removals = []

            for x in range(self.map_config['width']):
                for y in range(self.map_config['height']):
                    # Variables auxiliaires pour ajouts/retraits
                    add_var = LpVariable(
                        f"add_{x}_{y}_{t}", lowBound=0, cat='Integer')
                    remove_var = LpVariable(
                        f"remove_{x}_{y}_{t}", lowBound=0, cat='Integer')

                    if t == 0:
                        prev_biomass = initial_biomass[x][y]
                    else:
                        prev_biomass = biomass[x, y, t-1]

                    model += biomass[x, y, t] == prev_biomass + \
                        add_var - remove_var

                    additions.append(add_var)
                    removals.append(remove_var)

            # Actions < budget
            model += lpSum(additions) + \
                lpSum(removals) <= self.map_config['maxBiomassPerTurn']

        # Constrainte: Biomasse totale
        for t in range(horizon):
            model += lpSum([biomass[x, y, t]
                           for x in range(self.map_config['width'])
                           for y in range(self.map_config['height'])]) <= self.map_config['totalBiomass']

        # Solve
        print(f"  Building model with {len(model.variables())} variables...")
        status = model.solve(PULP_CBC_CMD(msg=1, timeLimit=time_limit))

        if status != 1:
            return None

        # Extraire actions pour chaque tick dans le chunk
        chunk_actions = {}
        for t in range(horizon):
            actions = []
            actual_tick = start_tick + t

            for x in range(self.map_config['width']):
                for y in range(self.map_config['height']):
                    if t == 0:
                        current = initial_biomass[x][y]
                    else:
                        current = int(value(biomass[x, y, t-1]))

                    target = int(value(biomass[x, y, t]))
                    diff = target - current

                    if diff > 0:
                        actions.append({
                            'type': 'ADD_BIOMASS',
                            'position': {'x': x, 'y': y},
                            'amount': diff
                        })
                    elif diff < 0:
                        actions.append({
                            'type': 'REMOVE_BIOMASS',
                            'position': {'x': x, 'y': y},
                            'amount': -diff
                        })

            chunk_actions[actual_tick] = actions

        return chunk_actions

    def _generate_paths(self):
        paths = []
        colonies = self.map_config['colonies']
        colony_positions = {(c['position']['x'], c['position']['y'])
                            for c in colonies}

        for i in range(len(colonies)):
            for j in range(i + 1, len(colonies)):
                positions = self._manhattan_path(colonies[i], colonies[j])

                # Filtrer les colonies (ne pas placer de biomasse)
                filtered_positions = [
                    p for p in positions
                    if (p.x, p.y) not in colony_positions
                ]

                path = type('Path', (), {
                    'colony1': colonies[i],
                    'colony2': colonies[j],
                    'positions': filtered_positions
                })()
                paths.append(path)
        return paths

    def _manhattan_path(self, col1, col2):
        path = []
        x, y = col1['position']['x'], col1['position']['y']
        end_x, end_y = col2['position']['x'], col2['position']['y']

        while x != end_x or y != end_y:
            if x < end_x:
                x += 1
            elif x > end_x:
                x -= 1
            elif y < end_y:
                y += 1
            elif y > end_y:
                y -= 1
            if x != end_x or y != end_y:
                path.append(type('Pos', (), {'x': x, 'y': y})())
        return path

    def _predict_colony_value(self, path, tick):
        val1 = self._colony_value_at_tick(path.colony1, tick)
        val2 = self._colony_value_at_tick(path.colony2, tick)
        return min(val1, val2)

    # Basé sur l'observation de la fluctuation des valeurs des colonies
    def _colony_value_at_tick(self, colony, tick):
        phase = colony.get('phaseShift', 0)
        period = 20
        amplitude = 5
        base = 10

        # Pattern sinusoïdal
        value = base + amplitude * \
            math.sin(2 * math.pi * (tick / period + phase))
        return max(1, int(value))


def save_solution(solution, filename):
    with open(filename, 'w') as f:
        json.dump(solution, f, indent=2)
    print(f"\n✓ Solution saved to {filename}")


def load_solution(filename):
    with open(filename, 'r') as f:
        return json.load(f)
