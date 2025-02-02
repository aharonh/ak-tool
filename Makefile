.PHONY: all install dev-install freeze test lint format format-docstrings coverage build publish docs docs-serve sbom

# Default 'all' runs install + test
all: install test

# Installs from pinned versions in requirements.txt
install:
	pip install .

# Installs latest main + dev extras dependencies
dev-install:
	pip install .[dev]
	curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b ~/bin

# Freezes current environment into requirements.txt
freeze:
	pip freeze > requirements.txt

dev-freeze:
	pip freeze > requirements-dev.txt

test:
	pytest tests/ --verbose

lint:
	flake8 src tests/

format:
	black src tests/
	docformatter --in-place --wrap-summaries 88 --wrap-descriptions 88 -r . || true

coverage:
	pytest --cov=src/ak_tool --cov-report=xml

build:
	flit build

publish:
	flit publish

# Build Sphinx documentation from the 'docs' directory
docs:
	sphinx-build -b html docs docs/_build/html

# Optionally, serve the docs locally for preview
docs-serve:
	sphinx-build -b html docs docs/_build/html && python -m http.server --directory docs/_build/html

sbom:
	syft ./.venv -o cyclonedx-json=sbom.json

bumpversion:
	bump2version patch
