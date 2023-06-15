.SUFFIXES:
.ONESHELL:

SHELL = /bin/bash
.SHELLFLAGS += -e

PYTHON = python3

BUILD_ENV = host

VENV = env

-include config.mk

ifeq ($(BUILD_ENV), venv)
ENV_TARGET = $(VENV)/pyvenv.cfg
ACTIVATE = source $(VENV)/bin/activate
else
ENV_TARGET = /dev/null
ACTIVATE = which $(PYTHON)
endif

.PHONY: all
all: check

ifeq ($(BUILD_ENV), venv)
$(ENV_TARGET): pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE)
	which $(PYTHON)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[test,dev]
else
$(ENV_TARGET):
endif

.PHONY: venv
venv: $(ENV_TARGET)

.PHONY: check
check: $(ENV_TARGET)
	$(ACTIVATE)
	$(PYTHON) -m unittest discover -v -s tests

.PHONY: coverage
coverage: $(ENV_TARGET)
	$(ACTIVATE)
	$(PYTHON) -m coverage run -m unittest discover -v -s tests
	$(PYTHON) -m coverage xml

.PHONY: lint
lint: $(ENV_TARGET)
	$(ACTIVATE)
	$(PYTHON) -m flake8 --config .flake8
	$(PYTHON) -m pylint tartarus tests

.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf *.egg-info
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name '__pycache__' -exec rm -r {} +
