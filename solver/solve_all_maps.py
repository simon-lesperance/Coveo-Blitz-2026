#!/usr/bin/env python3

from offline_solver import OfflineSolver, save_solution
from map_parser import parse_all_maps
import time
import os


def solve_all_maps(maps_dir='maps', output_dir='solutions', chunk_size=None, threads=0):
    """
    Résout toutes les cartes en utilisant Gurobi (ou CBC si Gurobi n'est pas disponible)

    Arguments:
        maps_dir: Répertoire contenant les fichiers de carte TMX et JSON
        output_dir: Répertoire pour enregistrer les solutions
        chunk_size: Ticks par chunk (none = résoudre le jeu entier d'un coup)
                    Les chunks plus petits sont plus rapides mais moins optimaux.
                    Petit: 30-60, Moyen: 70-100, Grand: 150+, None: 350
        threads: Nombre de threads à utiliser (0 = auto)

    Usage:
        python solve_all_maps.py # Résout toutes les cartes avec les paramètres par défaut
        python solve_all_maps.py --chunk=100 --threads=8 # Utilise des chunks de 100 ticks et 8 threads
        pyton solve_all_maps.py CrossRoads # Résout une seule carte avec les paramètres par défaut
        python solve_all_maps.py CrossRoads maps 1200 # Résout une seule carte avec une limite de temps personnalisée
        python solve_all_maps.py --chunk=none # Résout toutes les cartes en une seule fois (très très très long)
    """

    os.makedirs(output_dir, exist_ok=True)

    print("Parsing map configurations...")
    configs = parse_all_maps(maps_dir, use_real_data=True)

    if not configs:
        print("ERROR: No maps found!")
        return {}

    results = {}
    total_start = time.time()

    for map_name, config in configs.items():
        print(f"\n{'='*70}")
        print(f"Starting: {map_name}")
        print(f"{'='*70}")

        default_chunk, time_limit = get_safe_settings(config)
        actual_chunk = chunk_size if chunk_size is not None else default_chunk

        print(f"Settings: chunk_size={actual_chunk if actual_chunk else 'FULL'}, time_limit={
              time_limit}s, threads={threads if threads > 0 else 'auto'}")

        start_time = time.time()

        try:
            solver_obj = OfflineSolver(
                config, chunk_size=actual_chunk, threads=threads)
            solution = solver_obj.solve_full_game(
                time_limit_per_chunk=time_limit)

            elapsed = time.time() - start_time

            if solution:
                filename = os.path.join(output_dir, f"{map_name}.json")
                save_solution(solution, filename)

                total_actions = sum(len(actions)
                                    for actions in solution['actions'].values())

                results[map_name] = {
                    'status': 'SUCCESS',
                    'time': elapsed,
                    'total_actions': total_actions,
                    'file': filename,
                    'used_real_data': solver_obj.using_real_data
                }

                print(f"\nSUCCESS Solved in {elapsed/60:.1f} minutes")
                print(f"  Total actions: {total_actions}")
            else:
                results[map_name] = {'status': 'FAILED', 'time': elapsed}
                print(f"\nÃ¢Å“â€” Failed after {elapsed/60:.1f} minutes")

        except Exception as e:
            elapsed = time.time() - start_time
            results[map_name] = {'status': 'ERROR',
                                 'time': elapsed, 'error': str(e)}
            print(f"\nÃ¢Å“â€” Error: {e}")

            # Cooldown pour éviter des problèmes avec la licence de gurobi
        if map_name != list(configs.keys())[-1]:
            print("\nCooldown: 60 seconds...")
            time.sleep(60)

    # Sommaire des résultats
    # TODO


def get_safe_settings(config):
    # Paramètres par défaut
    total_biomass = config['totalBiomass']
    difficulty = config['difficulty']

    # RhythmicRings
    if total_biomass <= 10:
        return 40, 360

    # Easy small maps
    elif difficulty == 'easy' and total_biomass <= 32:
        return 60, 420

    # Easy larger maps
    elif difficulty == 'easy':
        return 70, 480

    # Medium maps
    elif difficulty == 'medium':
        return 60, 420

    # Hard maps
    else:
        return 50, 360


def solve_single_map(map_name, maps_dir='maps', output_dir='solutions', time_limit=600, chunk_size=None, threads=0):
    # Résout une seule carte spécifiée

    os.makedirs(output_dir, exist_ok=True)

    configs = parse_all_maps(maps_dir, use_real_data=True)

    if map_name not in configs:
        print(f"Error: Map '{map_name}' not found")
        print(f"Available maps: {', '.join(configs.keys())}")
        return None

    config = configs[map_name]

    print(f"Solving {map_name}...")
    print(f"  Size: {config['width']}x{config['height']}")
    print(f"  Difficulty: {config['difficulty']}")
    print(f"  Colonies: {len(config['colonies'])}")
    print(f"  Threads: {threads if threads > 0 else 'auto'}")

    default_chunk, _ = get_safe_settings(config)
    actual_chunk = chunk_size if chunk_size is not None else default_chunk
    print(f"  Chunk size: {
          actual_chunk if actual_chunk else 'FULL (351 ticks)'}")

    solver_obj = OfflineSolver(
        config, chunk_size=actual_chunk, threads=threads)
    solution = solver_obj.solve_full_game(time_limit_per_chunk=time_limit)

    if solution:
        filename = os.path.join(output_dir, f"{map_name}.json")
        save_solution(solution, filename)
        return solution
    else:
        print("Failed to solve")
        return None


if __name__ == "__main__":
    import sys

    print("="*70)
    print("\nUsing Gurobi solver (with CBC fallback)")
    print("\nChunk sizes: Trade-off between optimality and performance")
    print("  - Smaller chunks (30-60): Faster, but may miss long-term strategies")
    print("  - Larger chunks (100+): Better solutions, but much slower")
    print("  - None (full 351 ticks): Mathematically optimal, but VERY slow\n")

    threads = 0
    chunk_size = None  # Use defaults

    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    for arg in sys.argv[1:]:
        if arg.startswith('--chunk='):
            val = arg.split('=')[1]
            chunk_size = None if val.lower() == 'none' else int(val)
        elif arg.startswith('--threads='):
            threads = int(arg.split('=')[1])

    if len(args) > 0:
        map_name = args[0]
        maps_dir = args[1] if len(args) > 1 else 'maps'
        time_limit = int(args[2]) if len(args) > 2 else 600
        solve_single_map(map_name, maps_dir=maps_dir, time_limit=time_limit,
                         chunk_size=chunk_size, threads=threads)
    else:
        print("Usage:")
        print("  python solve_all_maps.py                           # Solve all (default chunks)")
        print("  python solve_all_maps.py --chunk=100               # Use 100 tick chunks")
        print("  python solve_all_maps.py --chunk=none              # Solve full 351 ticks")
        print("  python solve_all_maps.py --threads=8               # Use 8 threads")
        print("  python solve_all_maps.py CrossRoads                # Solve one map")
        print("  python solve_all_maps.py CrossRoads maps 1200      # Custom time limit")
        print("\nPress Ctrl+C to cancel")

        try:
            input("\nPress Enter to start...")
        except KeyboardInterrupt:
            print("\nCancelled")
            sys.exit(0)

        solve_all_maps(chunk_size=chunk_size, threads=threads)
