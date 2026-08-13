"""Starts coverage measurement in subprocesses.

The cram tests drive the command line interface by running `python3 -m ananke`,
so the code they exercise runs in a subprocess that the parent's coverage does
not see.  Python imports `sitecustomize` at startup if it is importable, and
`coverage.process_startup()` begins measurement when COVERAGE_PROCESS_START
names a configuration file, so putting this directory on PYTHONPATH is enough
to measure those runs.

This is inert unless COVERAGE_PROCESS_START is set, and tolerates coverage not
being installed at all, as it is not in the Nix build.
"""

try:
    import coverage
except ImportError:
    pass
else:
    coverage.process_startup()
