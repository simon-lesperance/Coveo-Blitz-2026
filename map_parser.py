import xml.etree.ElementTree as ET
import os


def parse_tmx_map(tmx_file):
    # Extrait la configuration d'une carte
    tree = ET.parse(tmx_file)
    root = tree.getroot()

    width = int(root.get('width'))
    height = int(root.get('height'))

    # Trouve les colonies
    colony_layer = root.find(".//layer[@name='Colony']")
    if colony_layer is None:
        raise ValueError("No Colony layer found in TMX file")

    data = colony_layer.find('data')
    if data is None:
        raise ValueError("No data element found in Colony layer")

    data_text = data.text.strip()

    # Parse les données
    rows = []
    for line in data_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        values = []
        for val in line.split(','):
            val = val.strip()
            if val:
                values.append(int(val))
        if values:
            rows.append(values)

    # Valider dimensions
    if len(rows) != height:
        print(f"  Warning: Expected {height} rows, got {len(rows)}")

    # Extraire les colonies
    colonies = []
    for y in range(min(height, len(rows))):
        row = rows[y]
        for x in range(min(width, len(row))):
            if row[x] > 0:
                colonies.append({
                    'id': len(colonies),
                    'position': {'x': x, 'y': y},
                    'type': row[x]
                })

    # Parse metadata
    meta = root.find(".//objectgroup[@name='Meta']/properties")
    if meta is None:
        raise ValueError("No Meta properties found in TMX file")

    properties = {}
    for prop in meta.findall('property'):
        name = prop.get('name')
        value = prop.get('value')
        properties[name] = value

    # Ajouter les changement de valeurs
    for colony in colonies:
        phase_key = f"colony{colony['id']}PhaseShift"
        if phase_key in properties:
            colony['phaseShift'] = float(properties[phase_key])
        else:
            colony['phaseShift'] = 0.0

    config = {
        'name': properties.get('name', 'Unknown'),
        'difficulty': properties.get('difficulty', 'unknown'),
        'width': width,
        'height': height,
        'totalBiomass': int(properties.get('totalBiomass', 30)),
        'maxBiomassPerTurn': int(properties.get('maxBiomassPerTurn', 5)),
        'colonies': colonies
    }

    return config


def parse_all_maps(maps_directory='maps'):
    # Parse toutes les cartes .tmx dans le répertoire maps/
    configs = {}

    if not os.path.exists(maps_directory):
        print(f"Warning: Directory '{maps_directory}' not found")
        print("Using test configuration instead")
        return get_test_configs()

    tmx_files = [f for f in os.listdir(maps_directory) if f.endswith('.tmx')]

    if not tmx_files:
        print("No TMX files found, using test configuration")
        return get_test_configs()

    print(f"Found {len(tmx_files)} TMX files in {maps_directory}/")

    for tmx_file in sorted(tmx_files):
        try:
            filepath = os.path.join(maps_directory, tmx_file)
            config = parse_tmx_map(filepath)
            configs[config['name']] = config
            print(f"  ✓ {config['name']:20s} - {config['width']}x{config['height']}, {
                  len(config['colonies'])} colonies ({config['difficulty']})")
        except Exception as e:
            print(f"  ✗ Error parsing {tmx_file}: {e}")

    if not configs:
        print("\nNo maps successfully parsed, using test configuration")
        return get_test_configs()

    return configs


def get_test_configs():
    """Configuration hard-codées pour des tests"""
    return {
        'CrossRoads': {
            'name': 'CrossRoads',
            'difficulty': 'easy',
            'width': 9,
            'height': 9,
            'totalBiomass': 30,
            'maxBiomassPerTurn': 6,
            'colonies': [
                {'id': 0, 'position': {'x': 4, 'y': 4}, 'phaseShift': 0},
                {'id': 1, 'position': {'x': 7, 'y': 4}, 'phaseShift': 1},
                {'id': 2, 'position': {'x': 4, 'y': 1}, 'phaseShift': 0.5},
                {'id': 3, 'position': {'x': 4, 'y': 7}, 'phaseShift': 1.5},
                {'id': 4, 'position': {'x': 1, 'y': 4}, 'phaseShift': 0}
            ]
        },
        'OppositionDance': {
            'name': 'OppositionDance',
            'difficulty': 'easy',
            'width': 10,
            'height': 10,
            'totalBiomass': 45,
            'maxBiomassPerTurn': 9,
            'colonies': [
                {'id': 0, 'position': {'x': 1, 'y': 1}, 'phaseShift': 0},
                {'id': 1, 'position': {'x': 8, 'y': 1}, 'phaseShift': 1},
                {'id': 2, 'position': {'x': 8, 'y': 8}, 'phaseShift': 0},
                {'id': 3, 'position': {'x': 1, 'y': 8}, 'phaseShift': 1}
            ]
        },
        'QuarterWave': {
            'name': 'QuarterWave',
            'difficulty': 'easy',
            'width': 9,
            'height': 9,
            'totalBiomass': 32,
            'maxBiomassPerTurn': 8,
            'colonies': [
                {'id': 0, 'position': {'x': 5, 'y': 3}, 'phaseShift': 0},
                {'id': 1, 'position': {'x': 1, 'y': 7}, 'phaseShift': 0.5},
                {'id': 2, 'position': {'x': 3, 'y': 5}, 'phaseShift': 1},
                {'id': 3, 'position': {'x': 7, 'y': 1}, 'phaseShift': 1.5}
            ]
        },
        'CrescentGarden': {
            'name': 'CrescentGarden',
            'difficulty': 'hard',
            'width': 11,
            'height': 7,
            'totalBiomass': 35,
            'maxBiomassPerTurn': 7,
            'colonies': [
                {'id': 0, 'position': {'x': 5, 'y': 3}, 'phaseShift': 0},
                {'id': 1, 'position': {'x': 1, 'y': 3}, 'phaseShift': 1},
                {'id': 2, 'position': {'x': 9, 'y': 3}, 'phaseShift': 0},
                {'id': 3, 'position': {'x': 7, 'y': 1}, 'phaseShift': 1},
                {'id': 4, 'position': {'x': 3, 'y': 5}, 'phaseShift': 0.5},
                {'id': 5, 'position': {'x': 7, 'y': 5}, 'phaseShift': 1.5}
            ]
        },
        'TimingMaster': {
            'name': 'TimingMaster',
            'difficulty': 'medium',
            'width': 12,
            'height': 7,
            'totalBiomass': 36,
            'maxBiomassPerTurn': 8,
            'colonies': [
                {'id': 0, 'position': {'x': 9, 'y': 5}, 'phaseShift': 0},
                {'id': 1, 'position': {'x': 9, 'y': 1}, 'phaseShift': 0},
                {'id': 2, 'position': {'x': 2, 'y': 1}, 'phaseShift': 1},
                {'id': 3, 'position': {'x': 2, 'y': 5}, 'phaseShift': 0.5}
            ]
        },
        'RhythmicRings': {
            'name': 'RhythmicRings',
            'difficulty': 'medium',
            'width': 11,
            'height': 11,
            'totalBiomass': 9,
            'maxBiomassPerTurn': 3,
            'colonies': [
                {'id': 0, 'position': {'x': 5, 'y': 1}, 'phaseShift': 0},
                {'id': 1, 'position': {'x': 2, 'y': 2}, 'phaseShift': 1.75},
                {'id': 2, 'position': {'x': 8, 'y': 2}, 'phaseShift': 0.25},
                {'id': 3, 'position': {'x': 1, 'y': 5}, 'phaseShift': 1.5},
                {'id': 4, 'position': {'x': 9, 'y': 5}, 'phaseShift': 0.5},
                {'id': 5, 'position': {'x': 2, 'y': 8}, 'phaseShift': 1.25},
                {'id': 6, 'position': {'x': 8, 'y': 8}, 'phaseShift': 0.75},
                {'id': 7, 'position': {'x': 5, 'y': 9}, 'phaseShift': 1}
            ]
        }
    }


if __name__ == "__main__":
    configs = parse_all_maps()

    print(f"\n{'='*60}")
    print("PARSED CONFIGURATIONS")
    print(f"{'='*60}")

    for name, config in sorted(configs.items()):
        print(f"\n{name}:")
        print(f"  Size: {config['width']}x{config['height']}")
        print(f"  Difficulty: {config['difficulty']}")
        print(f"  Biomass: {config['totalBiomass']
                            } (max {config['maxBiomassPerTurn']}/turn)")
        print(f"  Colonies: {len(config['colonies'])}")
        for col in config['colonies']:
            print(f"    Colony {col['id']}: ({col['position']['x']}, {
                  col['position']['y']}) phase={col['phaseShift']}")
