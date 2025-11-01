# Coveo Blitz 2026 - Qualifications
## Mycelium Connection Network Challenge

## Équipe - Confidently Wrong
- Simon Lespérance
-
-

## Utilisation
1. Démarrer le serveur local: `make handler`
2. Démarrer le client: `make client`

Les deux peuvent être démarrés en même temps avec `make run` mais il est recommandé de le faire séparément pour faciliter le débogage.
Une fois le client démarré, l'interface graphique devrait s'ouvrir dans votre navigateur par défaut.

## Dépendances
- Challenge Hors ligne
- Python 3.10+
- websockets 15.0.1
- dataclasses-json 0.6.7

Le challenge peut être téléchargé via
```
wget https://blitznary.s3.amazonaws.com/challenge-bin/blitz-registration-challenge-linux-x64.zip
unzip blitz-registration-challenge-linux-x64.zip
rm -rf blitz-registration-challenge-linux-x64.zip
```

Les dépendances Python peuvent être installées via pip:
`pip install websockets dataclasses-json`

Ou sur Arch Linux via pacman:
`sudo pacman -S python-websockets python-dataclasses-json`
