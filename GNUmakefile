.SUFFIXES:
.ONESHELL:

SHELL = /bin/bash
.SHELLFLAGS += -e

VENV = env
VENV_TARGET = $(VENV)/pyvenv.cfg
VENV_ACTIVATE = $(VENV)/bin/activate

-include config.mk

.PHONY: all
all: check

$(VENV_TARGET): pyproject.toml
	python3 -m venv $(VENV)
	source $(VENV_ACTIVATE)
	which python
	python -m pip install --upgrade pip
	python -m pip install -e .[test,dev]

.PHONY: venv
venv: $(VENV_TARGET)

.PHONY: check
check: $(VENV_TARGET)
	source $(VENV_ACTIVATE)
	python -m unittest discover -v -s tests

.PHONY: coverage
coverage: $(VENV_TARGET)
	source $(VENV_ACTIVATE)
	python -m coverage run -m unittest discover -v -s tests
	python -m coverage xml

.PHONY: lint
lint: $(VENV_TARGET)
	source $(VENV_ACTIVATE)
	python -m flake8 --config .flake8
	python -m pylint tartarus tests

.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf *.egg-info
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name '__pycache__' -exec rm -r {} +
