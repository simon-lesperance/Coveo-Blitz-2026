from game_message import TeamGameState, AddBiomassAction, RemoveBiomassAction, Position
import json
import os


class Bot:
    #Lit les solutions pré-calculées et les exécute

    def __init__(self, solutions_dir='solutions'):
        self.solutions_dir = solutions_dir
        self.solution = None
        self.map_name = None
        self.initialized = False

    def get_next_move(self, game_message: TeamGameState):
        if not self.initialized:
            self._load_solution(game_message)
            self.initialized = True

        if self.solution is None:
            print("ERROR: No solution loaded, cannot proceed")
            return []

        tick = game_message.currentTickNumber

        # Lit actions pour le tick
        tick_str = str(tick)
        if tick_str not in self.solution['actions']:
            # Pas d'actions
            return []

        # Convertit les actions en objets
        actions = []
        for action_dict in self.solution['actions'][tick_str]:
            pos = Position(action_dict['position']
                           ['x'], action_dict['position']['y'])

            if action_dict['type'] == 'ADD_BIOMASS':
                for _ in range(action_dict['amount']):
                    actions.append(AddBiomassAction(position=pos, amount=1))
            else:
                for _ in range(action_dict['amount']):
                    actions.append(RemoveBiomassAction(position=pos, amount=1))

        if tick % 50 == 0:
            print(f"Tick {tick}: Executing {
                  len(actions)} pre-computed actions")

        return actions

    def _load_solution(self, game_message: TeamGameState):
        # Identifie la carte et charge la solution correspondante

        # Identify map by size and colony count
        width = game_message.map.width
        height = game_message.map.height
        num_colonies = len(game_message.map.colonies)

        # Map signatures (width, height, num_colonies) -> name
        signatures = {
            (9, 9, 5): 'CrossRoads',
            (10, 10, 4): 'OppositionDance',
            (9, 9, 4): 'QuarterWave',
            (11, 7, 5): 'CrescentGarden',
            (12, 7, 4): 'TimingMaster',
            (11, 11, 8): 'RhythmicRings'
        }

        signature = (width, height, num_colonies)
        map_name = signatures.get(signature, None)

        if map_name is None:
            print(f"ERROR: Unknown map signature: {signature}")
            return

        # Charge le fichier de solution
        solution_file = os.path.join(self.solutions_dir, f"{map_name}.json")

        if not os.path.exists(solution_file):
            print(f"ERROR: Solution file not found: {solution_file}")
            print("Run 'python solve_all_maps.py' first to generate solutions")
            return

        with open(solution_file, 'r') as f:
            self.solution = json.load(f)

        self.map_name = map_name
        print(f"\n{'='*60}")
        print(f"Loaded optimal solution for: {map_name}")
        print(f"Solution contains {
              len(self.solution['actions'])} ticks of actions")
        print(f"{'='*60}\n")


class HybridPlaybackBot:
    """Uses pre-computed solution if available, otherwise falls back to heuristic"""

    def __init__(self, solutions_dir='solutions', fallback_bot=None):
        self.playback_bot = Bot(solutions_dir)
        self.fallback_bot = fallback_bot
        self.using_playback = True

    def get_next_move(self, game_message: TeamGameState):
        """Try playback first, fallback to heuristic if needed"""

        if self.using_playback:
            try:
                actions = self.playback_bot.get_next_move(game_message)
                if actions or game_message.currentTickNumber == 0:
                    return actions
                else:
                    # No actions but solution loaded - this is fine
                    return []
            except Exception as e:
                print(f"Playback failed: {e}")
                self.using_playback = False

        if self.fallback_bot:
            return self.fallback_bot.get_next_move(game_message)
        else:
            return []


# For easy integration - just import this
def create_bot(solutions_dir='solutions'):
    """Create the appropriate bot"""

    # Check if solutions exist
    if os.path.exists(solutions_dir) and any(f.endswith('.json') for f in os.listdir(solutions_dir)):
        print("Using pre-computed optimal solutions")
        return Bot(solutions_dir)
    else:
        print("WARNING: No pre-computed solutions found")
        print("Run: python solve_all_maps.py")
        print("Falling back to heuristic bot")

        # Import and use original bot
        try:
            from bot import Bot
            return Bot()
        except ImportError:
            print("ERROR: Could not import fallback bot")
            return None
