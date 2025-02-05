.PHONY: all install dev-install freeze test lint format coverage build publish docs docs-serve sbom docs-deploy

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

# Build Sphinx docs into docs/_build/html
docs:
	sphinx-build -b html docs docs/_build/html

# Optionally, serve the docs locally for preview
docs-serve:
	sphinx-build -b html docs docs/_build/html && python -m http.server --directory docs/_build/html

sbom:
	syft ./.venv -o cyclonedx-json=sbom.json

bumpversion:
	bump2version patch

# -----------------------------
# Push the built docs to gh-pages
# -----------------------------
docs-deploy: docs
	# Make sure docs/_build/html is committed. The '|| true' prevents errors if no changes are detected.
	git add docs/_build/html || true
	git commit -m "Update built docs" || true

	# 1) Create a local split branch from the subtree.
	git subtree split --prefix docs/_build/html -b gh-pages-split

	# 2) Force-push that split branch to the gh-pages branch on origin.
	git push -f origin gh-pages-split:gh-pages

	# 3) Clean up the temporary local branch.
	git branch -D gh-pages-split
