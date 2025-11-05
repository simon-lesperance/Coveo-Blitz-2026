HANDLER_DIR=linux-x64/
GREEDY_DIR=greedy_bot/
PARSER_DIR=parser_bot/
SOLVER_DIR=solver/
STAGING_DIR=staging/
CORE_DIR=core/
HANDLER=blitz-challenge-linux
BOT=bot.py
APPLICATION=application.py
LOCAL_ADDRESS=http://localhost:8765/


run:
	@echo "Running Handler in background"
	@$(MAKE) handler &
	sleep 2
	@echo "Select a bot to run:"
	@echo "1) Greedy Bot"
	@echo "2) Parser Bot"
	@read -p "Enter choice (1 or 2): " choice; \
	if [ "$$choice" -eq 1 ]; then \
		$(MAKE) greedy; \
	elif [ "$$choice" -eq 2 ]; then \
		$(MAKE) parser; \
	else \
		echo "Invalid choice. Please select 1 or 2."; \
	fi

handler: ${HANDLER_DIR}${HANDLER} 
	@echo "Running Mycellium Connection Challenge..."
	@echo "Starting handler..."
	@echo "Opening UI at $LOCAL_ADDRESS"
	@xdg-open $(LOCAL_ADDRESS)
	@cd ${HANDLER_DIR} && ./$(HANDLER)

greedy: ${GREEDY_DIR} setup
	@echo "Starting Greedy Bot..."
	@cp -r ${GREEDY_DIR}* ${STAGING_DIR}
	@cd ${STAGING_DIR} && mv greedy_bot.py ${BOT}
	@cd ${STAGING_DIR} && python3 ${APPLICATION}

parser: ${PARSER_DIR} setup
	@echo "Starting Parser Bot..."
	@cp -r ${PARSER_DIR}* ${STAGING_DIR}
	@cd ${STAGING_DIR} && mv parser_bot.py ${BOT}
	@cd ${STAGING_DIR} && python3 ${APPLICATION}

clean:
	@echo "Cleaning staging directory..."
	@rm -rf ${STAGING_DIR}*

setup:
	@echo "Setting up staging directory..."
	@mkdir -p ${STAGING_DIR}
	@cp -r ${CORE_DIR}* ${STAGING_DIR}
