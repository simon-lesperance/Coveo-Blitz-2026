HANDLER_DIR=linux-x64/
HANDLER=blitz-challenge-linux
BOT=bot.py
APPLICATION=application.py
LOCAL_ADDRESS=http://localhost:8765/

all: run

handler: ${HANDLER_DIR}${HANDLER}
	@echo "Running Mycellium Connection Challenge..."
	@echo "Starting handler..."
	@cd ${HANDLER_DIR} && ./$(HANDLER)

application: ${APPLICATION}
	@echo "Opening UI at $LOCAL_ADDRESS"
	@xdg-open $(LOCAL_ADDRESS)
	@echo "Starting application..."
	@python3 ${APPLICATION}

run: ${HANDLER_DIR}${HANDLER} ${BOT} ${APPLICATION}
	@echo "Running Mycellium Connection Challenge..."
	@echo "Starting handler..."
	@cd ${HANDLER_DIR} && ./$(HANDLER) &
	@echo "Opening UI at $LOCAL_ADDRESS"
	@xdg-open $(LOCAL_ADDRESS)
	@echo "Starting application..."
	@python3 ${APPLICATION}

