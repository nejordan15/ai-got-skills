PLUGIN := plugins/atlassian
PY := python3

.PHONY: help test unit integration lint clean

help:
	@echo "Targets:"
	@echo "  make unit         Run unit tests (mocked, no network)"
	@echo "  make integration  Run the live Confluence lifecycle test"
	@echo "                    (needs ATLASSIAN_* env vars + INTEGRATION_TEST_SPACE;"
	@echo "                     skips if unset — really creates/deletes pages)"
	@echo "  make lint         Lint with ruff"
	@echo "  make test         Alias for 'unit'"
	@echo "  make clean        Remove __pycache__ and .pyc files"

test: unit

unit:
	$(PY) -m unittest discover -s $(PLUGIN)/tests/unit -v

integration:
	@if [ -f local-integration-tests.env ]; then \
		echo "Loading local-integration-tests.env"; \
		set -a; . ./local-integration-tests.env; set +a; \
	fi; \
	$(PY) -m unittest discover -s $(PLUGIN)/tests/integration -v

lint:
	@command -v ruff >/dev/null 2>&1 || { echo "ruff not found — install with: pip3 install --user -r requirements-dev.txt"; exit 1; }
	ruff check $(PLUGIN)

clean:
	find $(PLUGIN) -name '__pycache__' -type d -prune -exec rm -rf {} +
	find $(PLUGIN) -name '*.pyc' -delete
