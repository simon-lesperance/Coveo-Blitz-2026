# Coveo Blitz 2026 - Qualifications
## Mycelium Connection Network Challenge

## Équipe - Confidently Wrong
- Simon Lespérance
-
-

## Utilisation
1. Démarrer le serveur local: `make handler`
2. Démarrer le client: `make bot`

Les deux peuvent être démarrés en même temps avec `make run` mais il est recommandé de le faire séparément pour faciliter le débogage.
Une fois le client démarré, l'interface graphique devrait s'ouvrir dans votre navigateur par défaut.

## Dépendances
- Challenge Hors ligne
- Python 3.10+
- websockets 15.0.1
- dataclasses-json 0.6.7
- PuLP 2.7.0 (pour la méthode basée sur la programmation linéaire)

Le challenge peut être téléchargé via
```
wget https://blitznary.s3.amazonaws.com/challenge-bin/blitz-registration-challenge-linux-x64.zip
unzip blitz-registration-challenge-linux-x64.zip
rm -rf blitz-registration-challenge-linux-x64.zip
```

Les dépendances Python peuvent être installées via pip:
`pip install websockets dataclasses-json pulp`

Ou sur Arch Linux via pacman:
`yay -S python-websockets python-dataclasses-json python-pulp`

## Bot "Greedy"
Le fichier `greedy_bot.py` contient un bot utilisant un algorithme glouton. Le fichier application ne devrait pas être modifié. Pour utiliser un bot différent, renomez le fichier en `bot.py`.

### Stratégie
Le bot implémente la stratégie suivante:
1. Il identifie tous les chemins possibles entre les colonies.
2. Il calcule le coût marginal et la profitabilité de chaque chemin.
3. Il attribue la biomasse en priorisant les chemins en cours.
4. Il identifie et enlève la biomasse excédentaire.

### Classes
- `Bot`: Classe principale du bot 
    - Point d'entrée pour la logique du bot
    - Fais les appels aux autres classes
    - Garde en mémoire les chemins et leur état
- `Path`: Représente un chemin entre deux colonies
    - Estime la valeur du chemin en fonction des valeurs futures
    - Calcule l'efficacité du chemin
- `Strategy`: Contient les fonctions de stratégie
    - Identifie les chemins prioritaires
    - Identifie les chemins moins profitables
    - Identifie les tuilles nécessitant de la biomasse
    - Calcule la biomasse excédentaire

Il y a beaucoup de paramètres qui peuvent êtres ajustés pour affiner le comportement du bot. En ce moment ils sont codés en dur dans les classes, mais ils pourraient être extraits. Notamment:
    - `MIN_VALUE_THRESHOLD` (Stratégie): Valeur minimale pour qu'un chemin soit considéré
    - `should_abandon_path` (Stratégie): Les ratios pour abandonner un chemin
    - `get_value()` (Path): La fonction contient le nombre de tour pour la valeur future


## Méthode basée sur la programmation linéaire
### Classes
- `solve_all_maps.py`: Script principal pour calculer les solutions.
    - Usage: `python solve_all_maps.py [nom_carte] <limite_temps>
    - Gère les entrées/sorties et fais les appels aux autres classes
- `map_parser.py`: Lit et analyse les fichiers de carte.
    - Lit les fichiers de carte et extrait les informations nécessaires.
    - Par défaut, lit les fichiers du dossier `maps/`.
    - Contient des copies des cartes (pour tests)
- `offline_solver.py`: Contient la logique principale pour résoudre le problème.
    - Utilise `PuLP` pour formuler et résoudre le problème de programmation linéaire.
    - Définit les variables, contraintes et la fonction objectif.
    - Contient les valeurs pour ajuster le comportement du solveur.

### Stratégie
On définit le problème de la façon suivante:
- Variables:
    - Biomasse(x, y, t): Quantité de biomasse sur une tuile (x, y) au tick t
    - Flow(i, t): Flux de biomasse sur le chemin i au tick t

- Contraintes:
    - La biomasse doit être sur un chemin (flow)
    - Le nombre d'action doit respecter le budget
    - La biomasse totale doit respecter la capacité maximale

- Objectif:
    - Maximiser le score total en fonction des connections entre paires de colonies.
