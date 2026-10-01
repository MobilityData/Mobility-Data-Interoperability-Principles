PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean:
	rm -rf generated/

setup:
	pip3 install --force-reinstall -r requirements.txt && \
	pip3 install --upgrade --force-reinstall properdocs && \
	pip3 install --upgrade --force-reinstall mkdocs-material

serve: clean
	@echo "Starting ProperDocs server..."
	@trap 'echo "Stopping ProperDocs server..."; pkill -f "properdocs serve"' SIGINT SIGTERM; \
	properdocs serve -f config/en/properdocs.yml --dev-addr 127.0.0.1:8000 --watch overrides

build: clean
	mkdir -p generated  # Ensure the folder exists
	properdocs build -f config/en/properdocs.yml --clean

killserve:
	pkill -f "properdocs serve"
