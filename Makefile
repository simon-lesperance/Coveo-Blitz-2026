HANDLER_DIR=linux-x64/
HANDLER=blitz-challenge-linux
BOT=bot.py
APPLICATION=application.py
LOCAL_ADDRESS=http://localhost:8765/

all: run

run:
	@make handler &
	@sleep 2
	@make bot

handler: ${HANDLER_DIR}${HANDLER}
	@echo "Running Mycellium Connection Challenge..."
	@echo "Starting handler..."
	@cd ${HANDLER_DIR} && ./$(HANDLER)

bot: ${APPLICATION}
	@echo "Opening UI at $LOCAL_ADDRESS"
	@xdg-open $(LOCAL_ADDRESS)
	@echo "Starting application..."
	@python3 ${APPLICATION}

