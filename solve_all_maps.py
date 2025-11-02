#!/usr/bin/env python3

from offline_solver import OfflineSolver, save_solution
from map_parser import parse_all_maps
import time
import os


def solve_all_maps(output_dir='solutions', time_limit_per_chunk=300):
    # Répertoire de sortie
    os.makedirs(output_dir, exist_ok=True)

    print("Parsing map configurations...")
    configs = parse_all_maps()

    results = {}
    total_start = time.time()

    # Calcule chaque carte
    for map_name, config in configs.items():
        print(f"\n{'='*70}")
        print(f"Starting: {map_name}")
        print(f"{'='*70}")

        start_time = time.time()

        solver = OfflineSolver(config)
        solution = solver.solve_full_game(
            time_limit_per_chunk=time_limit_per_chunk)

        elapsed = time.time() - start_time

        if solution:
            # Sauvegarde
            filename = os.path.join(output_dir, f"{map_name}.json")
            save_solution(solution, filename)

            total_actions = sum(len(actions)
                                for actions in solution['actions'].values())

            results[map_name] = {
                'status': 'SUCCESS',
                'time': elapsed,
                'total_actions': total_actions,
                'file': filename
            }

            print(f"\n✓ {map_name} solved in {elapsed:.1f}s")
            print(f"  Total actions: {total_actions}")
        else:
            results[map_name] = {
                'status': 'FAILED',
                'time': elapsed
            }
            print(f"\n✗ {map_name} failed after {elapsed:.1f}s")

    total_elapsed = time.time() - total_start

    # Sommaire
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print()

    for map_name, result in results.items():
        status = "✓" if result['status'] == 'SUCCESS' else "✗"
        print(f"{status} {map_name:20s} - {result['time']/60:.1f}m")
        if result['status'] == 'SUCCESS':
            print(f"    {result['total_actions']} actions -> {result['file']}")

    success_count = sum(1 for r in results.values()
                        if r['status'] == 'SUCCESS')
    print(f"\n{success_count}/{len(results)} maps solved successfully")

    return results


def solve_single_map(map_name, output_dir='solutions', time_limit=1800):
    # Une seule carte (pour test)
    # python solve_all_maps.py <nom_de_la_carte> [limite_de_temps]

    os.makedirs(output_dir, exist_ok=True)

    configs = parse_all_maps()

    if map_name not in configs:
        print(f"Error: Map '{map_name}' not found")
        print(f"Available maps: {', '.join(configs.keys())}")
        return None

    config = configs[map_name]

    print(f"Solving {map_name}...")
    print(f"  Size: {config['width']}x{config['height']}")
    print(f"  Difficulty: {config['difficulty']}")
    print(f"  Colonies: {len(config['colonies'])}")

    solver = OfflineSolver(config)
    solution = solver.solve_full_game(time_limit_per_chunk=time_limit)

    if solution:
        filename = os.path.join(output_dir, f"{map_name}.json")
        save_solution(solution, filename)
        return solution
    else:
        print("Failed to solve")
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Une carte spécifique
        map_name = sys.argv[1]
        time_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 600
        solve_single_map(map_name, time_limit=time_limit)
    else:
        # Toutes
        print("This will solve all 6 maps (may take 1-3 hours)")
        print("Press Ctrl+C to cancel")

        try:
            input("\nPress Enter to start...")
        except KeyboardInterrupt:
            print("\nCancelled")
            sys.exit(0)

        solve_all_maps(time_limit_per_chunk=600)
