#!/bin/bash
# Démarre le programme et lance un des deux bots.
#
BOT_PID=0
HANDLER_PID=0


echo "Démarrage du Handler en arrière-plan..."
make handler &
HANDLER_PID=$!
sleep 2
echo "Sélectionnez un bot à exécuter :"
echo "1) Greedy Bot"
echo "2) Parser Bot"
read -p "Entrez votre choix (1 ou 2) : " choice
if [ "$choice" -eq 1 ]; then
		make greedy
elif [ "$choice" -eq 2 ]; then
		make parser
else
		echo "Choix invalide. Veuillez sélectionner 1 ou 2."
fi

BOT_PID=$!
wait $BOT_PID
echo "Arrêt du Handler..."
kill $HANDLER_PID
