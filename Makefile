PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean:
	rm -rf generated/

setup:
	pip3 install --force-reinstall -r requirements.txt && \
	pip3 install --upgrade --force-reinstall mkdocs-material

# --watch: mkdocs only watches docs/ and the config by itself, so the
# specification registry's sources (hooks/, scripts/, data/) have to be named. Note that mkdocs caches
# the hook module -- an edit to hooks/ or scripts/ triggers a rebuild but the
# old code runs, so restart the server after changing those.
serve: clean
	@echo "Starting MkDocs server..."
	@trap 'echo "Stopping MkDocs server..."; pkill -f "mkdocs serve"' SIGINT SIGTERM; \
	mkdocs serve -f config/en/mkdocs.yml --dev-addr 127.0.0.1:8000 \
		--watch overrides --watch hooks --watch scripts --watch data

build: clean
	mkdir -p generated  # Ensure the folder exists
	mkdocs build -f config/en/mkdocs.yml --clean

killserve:
	pkill -f "mkdocs serve"

# --- Specification registry (/specifications) -------------------------------
# The pages and the /api/ files are built from data/ (see data/README.md).

specs-check: ## Validate the registry files in data/ and print the display order
	python3 scripts/check_specs.py

specs-export: ## Write the API files (JSON catalogue, full export CSV) to generated/
	python3 scripts/check_specs.py --export generated
