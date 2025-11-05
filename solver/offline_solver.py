from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, value
try:
    from pulp import GUROBI_CMD
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
from game_message import Position, GameMap, Colony, AddBiomassAction, RemoveBiomassAction
import json
import math


class OfflineSolver:
    """ Solver pour le challenge qui utilise la programmation linéaire.
    Utilise PuLP et Gurobi/CBC pour résoudre le problème d'optimisation.
    """

    def __init__(self, map_config, chunk_size=None, threads=0):
        self.map_config = map_config
        self.total_ticks = 351
        self.paths = []
        self.using_real_data = self._check_has_real_data()
        self.chunk_size = chunk_size  # None = solve entire game at once
        self.threads = threads

    def _check_has_real_data(self):
        if not self.map_config['colonies']:
            return False

        first_colony = self.map_config['colonies'][0]
        has_data = 'futureNutrients' in first_colony and first_colony['futureNutrients']

        if has_data:
            print(f"Using REAL futureNutrients data ({
                  len(first_colony['futureNutrients'])} ticks)")
        else:
            print(f"No real data - using formula prediction")

        return has_data

    def solve_full_game(self, time_limit_per_chunk=300):
        print(f"\n{'='*60}")
        print(f"Solving {self.map_config['name']} ({
              self.map_config['difficulty']})")
        print(f"{'='*60}")

        self.paths = self._generate_paths()
        print(f"Generated {len(self.paths)} paths between colonies")

        chunk_size = self.chunk_size or self._get_optimal_chunk_size()
        if self.chunk_size is None:
            print(f"Solving ENTIRE game ({
                  self.total_ticks} ticks) - may take a long time!")
            chunk_size = self.total_ticks
        else:
            print(f"Using chunk size: {chunk_size} ticks")

        all_actions = {}
        current_biomass = [[0] * self.map_config['height']
                           for _ in range(self.map_config['width'])]

        for start_tick in range(0, self.total_ticks, chunk_size):
            end_tick = min(start_tick + chunk_size, self.total_ticks)
            print(f"\nSolving ticks {start_tick}-{end_tick}...")

            chunk_actions, final_biomass = self._solve_chunk(
                start_tick,
                end_tick,
                current_biomass,
                time_limit_per_chunk
            )

            if chunk_actions is None:
                print(f"Failed to solve chunk {start_tick}-{end_tick}")
                return None

            for tick, actions in chunk_actions.items():
                all_actions[tick] = actions

            # Use actual final biomass state from solver
            current_biomass = final_biomass

            print(f"  Ã¢Å“â€œ Chunk solved, {
                  len(chunk_actions)} ticks planned")

        solution = {
            'map_name': self.map_config['name'],
            'total_ticks': self.total_ticks,
            'actions': all_actions
        }

        return solution

    def _get_optimal_chunk_size(self):
        # Détermine la taille des chunks en fonction de la quantité de biomasse
        total_biomass = self.map_config['totalBiomass']
        max_per_turn = self.map_config['maxBiomassPerTurn']

        if total_biomass <= 10:
            return 30
        elif total_biomass <= 20:
            return 40
        elif max_per_turn <= 5:
            return 45
        else:
            return 50

    def _solve_chunk(self, start_tick, end_tick, initial_biomass, time_limit):
        # Solve un chunk de ticks
        horizon = end_tick - start_tick
        model = LpProblem(f"Mycelium_{start_tick}_{end_tick}", LpMaximize)

        # Variables: Biomass [x, y, t] - Position, Tick
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

        # Variables Flow [chemin, t]
        flow = {}
        for i in range(len(self.paths)):
            for t in range(horizon):
                flow[i, t] = LpVariable(f"f_{i}_{t}", lowBound=0)

        # Variables: Actions Ajouter/enlever
        add_vars = {}
        remove_vars = {}

        for t in range(horizon):
            for x in range(self.map_config['width']):
                for y in range(self.map_config['height']):
                    add_vars[x, y, t] = LpVariable(
                        f"add_{x}_{y}_{t}", lowBound=0, cat='Integer')
                    remove_vars[x, y, t] = LpVariable(
                        f"remove_{x}_{y}_{t}", lowBound=0, cat='Integer')

        # Objectif: Maximiser la valeur totale des chemins entre colonies
        score_terms = []
        for t in range(horizon):
            actual_tick = start_tick + t
            for i, path in enumerate(self.paths):
                colony_value = self._predict_colony_value(path, actual_tick)
                score_terms.append(flow[i, t] * colony_value)

        model += lpSum(score_terms)

        # Contrainte: Flow limité par la biomasse sur les positions du chemin
        for t in range(horizon):
            for i, path in enumerate(self.paths):
                for pos in path.positions:
                    model += flow[i, t] <= biomass[pos.x, pos.y, t]

        # Constrainte: Quantité de biomasse cohérente entre les tours
        for t in range(horizon):
            for x in range(self.map_config['width']):
                for y in range(self.map_config['height']):
                    if t == 0:
                        prev_biomass = initial_biomass[x][y]
                    else:
                        prev_biomass = biomass[x, y, t-1]

                    model += biomass[x, y, t] == prev_biomass + \
                        add_vars[x, y, t] - remove_vars[x, y, t]

        # Constrainte: Limite de biomasse par tour
        for t in range(horizon):
            additions = [add_vars[x, y, t]
                         for x in range(self.map_config['width'])
                         for y in range(self.map_config['height'])]
            removals = [remove_vars[x, y, t]
                        for x in range(self.map_config['width'])
                        for y in range(self.map_config['height'])]

            model += lpSum(additions) + \
                lpSum(removals) <= self.map_config['maxBiomassPerTurn']

        # Constrainte: Limite totale de biomasse sur la carte
        for t in range(horizon):
            total_biomass = lpSum([biomass[x, y, t]
                                  for x in range(self.map_config['width'])
                                  for y in range(self.map_config['height'])])
            model += total_biomass <= self.map_config['totalBiomass']

            # Résolution avec Gurobi ou CBC
        print(f"  Building model with {len(model.variables())} variables...")

        if GUROBI_AVAILABLE:
            try:
                solver_cmd = GUROBI_CMD(
                    msg=1,
                    timeLimit=time_limit,
                    threads=self.threads if self.threads > 0 else None,
                    options=[
                        ('MIPGap', 0.001),
                        ('MIPFocus', 1),
                    ]
                )
                status = model.solve(solver_cmd)
                print(f"  Gurobi: Solved with status {status}")
            except Exception as e:
                print(f"  Gurobi failed: {e}, falling back to CBC")
                threads_arg = self.threads if self.threads > 0 else 4
                status = model.solve(PULP_CBC_CMD(
                    msg=1, timeLimit=time_limit, threads=threads_arg))
        else:
            print(f"  Gurobi not available, using CBC")
            threads_arg = self.threads if self.threads > 0 else 4
            status = model.solve(PULP_CBC_CMD(
                msg=1, timeLimit=time_limit, threads=threads_arg))

        if status != 1:
            print(f"  WARNING: Solver status = {status}")
            return None, None

        # Convertit les variables du solveur en actions
        chunk_actions = {}
        for t in range(horizon):
            actions = []
            actual_tick = start_tick + t

            for x in range(self.map_config['width']):
                for y in range(self.map_config['height']):
                    add_amount = int(round(value(add_vars[x, y, t]) or 0))
                    remove_amount = int(
                        round(value(remove_vars[x, y, t]) or 0))

                    if add_amount > 0:
                        actions.append({
                            'type': 'ADD_BIOMASS',
                            'position': {'x': x, 'y': y},
                            'amount': add_amount
                        })

                    if remove_amount > 0:
                        actions.append({
                            'type': 'REMOVE_BIOMASS',
                            'position': {'x': x, 'y': y},
                            'amount': remove_amount
                        })

            total_budget = sum(a['amount'] for a in actions)
            if total_budget > self.map_config['maxBiomassPerTurn']:
                print(f"  WARNING: Tick {actual_tick} exceeds budget: {
                      total_budget} > {self.map_config['maxBiomassPerTurn']}")

            chunk_actions[actual_tick] = actions

            # Simule l'état de la biomasse pour vérification des contraintes
        sim_biomass = [[initial_biomass[x][y] for y in range(self.map_config['height'])]
                       for x in range(self.map_config['width'])]

        for t in range(horizon):
            actual_tick = start_tick + t
            for action in chunk_actions[actual_tick]:
                x, y = action['position']['x'], action['position']['y']
                if action['type'] == 'ADD_BIOMASS':
                    sim_biomass[x][y] += action['amount']
                else:
                    sim_biomass[x][y] -= action['amount']

            total_sim = sum(sum(row) for row in sim_biomass)
            if total_sim > self.map_config['totalBiomass']:
                print(f"  ERROR at tick {actual_tick}: Simulated biomass {
                      total_sim} > limit {self.map_config['totalBiomass']}")

        final_biomass = [[0] * self.map_config['height']
                         for _ in range(self.map_config['width'])]

        for x in range(self.map_config['width']):
            for y in range(self.map_config['height']):
                final_biomass[x][y] = int(
                    round(value(biomass[x, y, horizon-1]) or 0))

                # Vérification finale
        total_from_solver = sum(sum(row) for row in final_biomass)
        total_from_sim = sum(sum(row) for row in sim_biomass)

        if total_from_solver > self.map_config['totalBiomass']:
            print(f"  ERROR: Solver final biomass {total_from_solver} > limit {
                  self.map_config['totalBiomass']}")

        if abs(total_from_solver - total_from_sim) > 1:
            print(
                f"  WARNING: Simulation mismatch - solver={total_from_solver}, sim={total_from_sim}")

        return chunk_actions, final_biomass

    def _generate_paths(self):
        paths = []
        colonies = self.map_config['colonies']
        colony_positions = {(c['position']['x'], c['position']['y'])
                            for c in colonies}

        for i in range(len(colonies)):
            for j in range(i + 1, len(colonies)):
                positions = self._manhattan_path(colonies[i], colonies[j])

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
        # Valeurs des colonies à partir des données obtenues par le data_bot
        val1 = self._get_colony_value(path.colony1, tick)
        val2 = self._get_colony_value(path.colony2, tick)
        return min(val1, val2)

    def _get_colony_value(self, colony, tick):
        if 'futureNutrients' in colony and colony['futureNutrients']:
            future_values = colony['futureNutrients']

            if tick < len(future_values):
                return future_values[tick]

            return future_values[-1]

        if 'nutrients' in colony:
            return colony['nutrients']

        return self._formula_prediction(colony, tick)

    def _formula_prediction(self, colony, tick):
        # Si pas de données, estimation par fonction sin
        # Surprenament près de la réalité pour certaines maps
        phase = colony.get('phaseShift', 0)
        period = 20
        amplitude = 5
        base = 10

        value = base + amplitude * \
            math.sin(2 * math.pi * (tick / period + phase))
        return max(1, int(value))


def save_solution(solution, filename):
    with open(filename, 'w') as f:
        json.dump(solution, f, indent=2)
    print(f"\nSolution saved to {filename}")


def load_solution(filename):
    with open(filename, 'r') as f:
        return json.load(f)
