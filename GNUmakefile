.SUFFIXES:
.ONESHELL:

SHELL = /bin/bash
.SHELLFLAGS += -e

PYTHON = python3

BUILD_ENV = host

VENV = env

VERSION = "0.1.0+$(shell git describe --always)"

-include config.mk

ifeq ($(BUILD_ENV), venv)
ENV_TARGET = $(VENV)/pyvenv.cfg
ACTIVATE = source $(VENV)/bin/activate
else
ENV_TARGET = /dev/null
ACTIVATE = which $(PYTHON)
BUILD_FLAGS = --no-isolation
endif

GENERATED = tartarus/version.py

.PHONY: all
all: generate

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

.PHONY: generate
generate: $(GENERATED)

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

tartarus/version.py: FORCE
	cat << EOF > $@
	"""This module contains version information."""
	# This file is auto-generated, do not edit by hand
	__version__ = $(VERSION)
	EOF

.git/hooks/post-commit: FORCE
	cat << EOF > $@
	#!/bin/sh
	echo "Generating version.py..."
	make tartarus/version.py >/dev/null
	EOF
	chmod +x $@

dist: generate
	$(PYTHON) -m build $(BUILD_FLAGS)

.PHONY: clean
clean:
	rm -f tartarus/version.py
	rm -rf $(VENV)
	rm -rf dist
	rm -rf *.egg-info
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name '__pycache__' -exec rm -r {} +

FORCE:
