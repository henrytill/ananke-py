.SUFFIXES:
.ONESHELL:

SHELL = /bin/bash
.SHELLFLAGS += -e

PYTHON = python3
MYPY = mypy

BUILD_ENV = host

VENV = env

VERSION = "0.1.0+$(shell git rev-parse --short HEAD)"

-include config.mk

define VERSION_PY =
\"\"\"This module contains version information.\"\"\"
# This file is auto-generated, do not edit by hand
__version__ = \"$(VERSION)\"
endef

define POST_COMMIT =
#!/bin/sh
echo \"Generating version.py...\"
make ananke/version.py >/dev/null
endef

ifeq ($(BUILD_ENV), venv)
ENV_TARGET = $(VENV)/pyvenv.cfg
ACTIVATE = source $(VENV)/bin/activate
else
ENV_TARGET = /dev/null
ACTIVATE = which $(PYTHON)
BUILD_FLAGS = --no-isolation
endif

GENERATED = \
	ananke/version.py

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
	$(MYPY) ananke
	$(MYPY) tests

.PHONY: test
test: $(ENV_TARGET)
	$(ACTIVATE)
	$(PYTHON) -m unittest discover -v -s tests
	$(PYTHON) -m doctest -v ananke/data/common.py

.PHONY: coverage
coverage: $(ENV_TARGET)
	$(ACTIVATE)
	$(PYTHON) -m coverage run -m unittest discover -v -s tests
	$(PYTHON) -m coverage xml

.PHONY: lint
lint: $(ENV_TARGET)
	$(ACTIVATE)
	$(PYTHON) -m flake8 --config .flake8
	$(PYTHON) -m pylint ananke tests

ananke/version.py: FORCE
	@echo "$(VERSION_PY)" > $@

.git/hooks/post-commit: FORCE
	@echo "$(POST_COMMIT)" > $@
	chmod +x $@

dist: generate
	$(PYTHON) -m build $(BUILD_FLAGS)

.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf dist
	rm -rf *.egg-info
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name '__pycache__' -exec rm -r {} +

FORCE:
