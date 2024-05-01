.PHONY: all format lint type-check configs

all: format lint type-check

#configs:
#	@echo "Generating config files..."
#	python tools/generate_exchange_configs.py

format:
	@echo "Formatting code..."
	ruff .

lint:
	@echo "Linting code..."
	ruff . --check
	flake8 .

type-check:
	@echo "Type checking..."
	mypy .
	pyright .

help:
	@echo "make configs       - Generate config files"
	@echo "make format       - Format the source code with ruff"
	@echo "make lint         - Lint the source code with ruff and flake8"
	@echo "make type-check   - Perform type checking with mypy"
	@echo "make all          - Perform format, lint, and type-check"