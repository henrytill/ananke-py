.SUFFIXES:

SHELL = /bin/bash

PYTHON3 = python3

VENV = env

.PHONY: all
all:

$(VENV)/pyvenv.cfg: pyproject.toml
	$(PYTHON3) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e .[test]

.PHONY: venv
venv: $(VENV)/pyvenv.cfg

.PHONY: test
test:
	$(PYTHON3) -m unittest discover -v -s tests

.PHONY: coverage
coverage:
	$(PYTHON3) -m coverage run -m unittest discover -v -s tests
	$(PYTHON3) -m coverage xml

.PHONY: clean
clean:
	rm -rf $(VENV)
	find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf tartarus.egg-info
	rm -f .coverage
	rm -f coverage.xml
