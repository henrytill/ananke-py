.SUFFIXES:
.ONESHELL:

SHELL = /bin/bash
.SHELLFLAGS += -e

BUILD_ENV = host

VENV = env

-include config.mk

ifeq ($(BUILD_ENV), venv)
ENV_TARGET = $(VENV)/pyvenv.cfg
ACTIVATE = source $(VENV)/bin/activate
else
ENV_TARGET = /dev/null
ACTIVATE = which python3
endif

.PHONY: all
all: check

ifeq ($(BUILD_ENV), venv)
$(ENV_TARGET): pyproject.toml
	python3 -m venv $(VENV)
	$(ACTIVATE)
	which python3
	python3 -m pip install --upgrade pip
	python3 -m pip install -e .[test,dev]
else
$(ENV_TARGET):
endif

.PHONY: venv
venv: $(ENV_TARGET)

.PHONY: check
check: $(ENV_TARGET)
	$(ACTIVATE)
	python3 -m unittest discover -v -s tests

.PHONY: coverage
coverage: $(ENV_TARGET)
	$(ACTIVATE)
	python3 -m coverage run -m unittest discover -v -s tests
	python3 -m coverage xml

.PHONY: lint
lint: $(ENV_TARGET)
	$(ACTIVATE)
	python3 -m flake8 --config .flake8
	python3 -m pylint tartarus tests

.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf *.egg-info
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name '__pycache__' -exec rm -r {} +
