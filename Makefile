# Makefile

.PHONY: all install dev-install freeze test lint format coverage build publish

# Default 'all' runs install + test
all: install test

# Installs from pinned versions in requirements.txt
install:
	pip install -r requirements.txt

# Installs latest main + dev extras dependencies
dev-install:
	pip install .[dev]

# Freezes current environment into requirements.txt
freeze:
	pip freeze > requirements.txt

test:
	pytest tests/ --verbose

lint:
	flake8 src tests/

format:
	black src tests/

coverage:
	pytest --cov=src/ak --cov-report=xml

build:
	flit build

publish:
	flit publish
