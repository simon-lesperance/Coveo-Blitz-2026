""" Module pour lire et analyser les fichiers TMX et charger les données des colonies"""

import xml.etree.ElementTree as ET
import os
import json


def parse_tmx_map(tmx_file):
    # Extrait la configuration d'une carte
    tree = ET.parse(tmx_file)
    root = tree.getroot()

    width = int(root.get('width'))
    height = int(root.get('height'))

    # Layer de colonies
    colony_layer = root.find(".//layer[@name='Colony']")
    if colony_layer is None:
        raise ValueError("No Colony layer found in TMX file")

    data = colony_layer.find('data')
    if data is None:
        raise ValueError("No data element found in Colony layer")

    data_text = data.text.strip()

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

    # Metadata
    meta = root.find(".//objectgroup[@name='Meta']/properties")
    if meta is None:
        raise ValueError("No Meta properties found in TMX file")

    properties = {}
    for prop in meta.findall('property'):
        name = prop.get('name')
        value = prop.get('value')
        properties[name] = value

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


def load_colony_data(colony_data_file):
    # Charge les données des colonies à partir d'un fichier JSON
    with open(colony_data_file, 'r') as f:
        data = json.load(f)
    return data['colonies']


def parse_all_maps(maps_directory='maps', use_real_data=True):
    """
    Charge tous les fichiers TMX. Optionellement, si les données receuillies 
    par le data_bot sont disponibles, charge les futureNutrients pour chaque colonies.
    Si jamais le répertoire n'existe pas ou qu'aucun fichier TMX n'est trouvé,
    utilise une configuration de test hardcodée.

    Args:
        maps_directory: Répertoire contenant les fichiers TMX et JSON
        use_real_data: Si True, tente de charger les données réelles des colonies
    """
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

            if use_real_data:
                colony_data_file = os.path.join(
                    maps_directory,
                    f"{config['name']}_colony_data.json"
                )

                if os.path.exists(colony_data_file):
                    real_colonies = load_colony_data(colony_data_file)
                    config['colonies'] = real_colonies
                    print(f"  ✓ {config['name']:20s} - {config['width']}x{config['height']}, {
                          len(config['colonies'])} colonies ({config['difficulty']}) [REAL DATA]")
                else:
                    print(f"  ⚠ {config['name']:20s} - {config['width']}x{config['height']}, {len(
                        config['colonies'])} colonies ({config['difficulty']}) [NO REAL DATA - using formula]")
            else:
                print(f"  ✓ {config['name']:20s} - {config['width']}x{config['height']}, {
                      len(config['colonies'])} colonies ({config['difficulty']})")

            configs[config['name']] = config

        except Exception as e:
            print(f"  ✗ Error parsing {tmx_file}: {e}")

    if not configs:
        print("\nNo maps successfully parsed, using test configuration")
        return get_test_configs()

    return configs


def get_test_configs():
    """ Valeurs de test hardcodées si aucun fichier TMX n'est trouvé """
    return {
        'CrossRoads': {
            'name': 'CrossRoads',
            'difficulty': 'easy',
            'width': 9,
            'height': 9,
            'totalBiomass': 30,
            'maxBiomassPerTurn': 6,
            'colonies': [
                {'id': 0, 'position': {'x': 4, 'y': 4}},
                {'id': 1, 'position': {'x': 7, 'y': 4}},
                {'id': 2, 'position': {'x': 4, 'y': 1}},
                {'id': 3, 'position': {'x': 4, 'y': 7}},
                {'id': 4, 'position': {'x': 1, 'y': 4}}
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
                {'id': 0, 'position': {'x': 1, 'y': 1}},
                {'id': 1, 'position': {'x': 8, 'y': 1}},
                {'id': 2, 'position': {'x': 8, 'y': 8}},
                {'id': 3, 'position': {'x': 1, 'y': 8}}
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
                {'id': 0, 'position': {'x': 5, 'y': 3}},
                {'id': 1, 'position': {'x': 1, 'y': 7}},
                {'id': 2, 'position': {'x': 3, 'y': 5}},
                {'id': 3, 'position': {'x': 7, 'y': 1}}
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
                {'id': 0, 'position': {'x': 5, 'y': 3}},
                {'id': 1, 'position': {'x': 1, 'y': 3}},
                {'id': 2, 'position': {'x': 9, 'y': 3}},
                {'id': 3, 'position': {'x': 7, 'y': 1}},
                {'id': 4, 'position': {'x': 3, 'y': 5}}
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
                {'id': 0, 'position': {'x': 9, 'y': 5}},
                {'id': 1, 'position': {'x': 9, 'y': 1}},
                {'id': 2, 'position': {'x': 2, 'y': 1}},
                {'id': 3, 'position': {'x': 2, 'y': 5}}
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
                {'id': 0, 'position': {'x': 5, 'y': 1}},
                {'id': 1, 'position': {'x': 2, 'y': 2}},
                {'id': 2, 'position': {'x': 8, 'y': 2}},
                {'id': 3, 'position': {'x': 1, 'y': 5}},
                {'id': 4, 'position': {'x': 9, 'y': 5}},
                {'id': 5, 'position': {'x': 2, 'y': 8}},
                {'id': 6, 'position': {'x': 8, 'y': 8}},
                {'id': 7, 'position': {'x': 5, 'y': 9}}
            ]
        }
    }


if __name__ == "__main__":
    import sys

    maps_dir = sys.argv[1] if len(sys.argv) > 1 else 'maps'
    configs = parse_all_maps(maps_dir, use_real_data=True)

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

        if config['colonies'] and 'futureNutrients' in config['colonies'][0]:
            future_len = len(config['colonies'][0]['futureNutrients'])
            print(f"  ✓ Has real futureNutrients data ({future_len} ticks)")
        else:
            print(f"  ⚠ No futureNutrients - will use formula")
