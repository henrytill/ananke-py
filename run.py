#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
import venv
from enum import Enum
from pathlib import Path
from typing import Optional

PACKAGE_NAME = "ananke"
TEST_DIR = "tests"
VENV_DIR = "env"

logger = logging.getLogger(__name__)


class Command(Enum):
    CREATE_ENV = "create-env"
    CHECK = "check"
    LINT = "lint"
    FMT = "fmt"
    TEST = "test"


def get_python(use_venv: bool) -> str:
    if use_venv:
        venv_path = Path(VENV_DIR)
        python = venv_path / "bin" / "python3"
        if not python.exists():
            logger.error("Virtual environment not found. Run './run.py create-env' first")
            sys.exit(1)
        return str(python)
    return sys.executable


def run(cmd: list[str], use_venv: bool = False, extra_env: Optional[dict[str, str]] = None):
    python = get_python(use_venv)
    if cmd[0] in ("python3", "python"):
        cmd[0] = python
    env = None
    if extra_env or use_venv:
        env = dict(os.environ)
        if use_venv:
            # cram invokes `python3` itself, which must resolve to the same
            # interpreter as everything else, not whatever is first on PATH.
            env["PATH"] = os.pathsep.join([str(Path(VENV_DIR).resolve() / "bin"), env.get("PATH", "")])
        env.update(extra_env or {})
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, env=env)
    if result.returncode != 0:
        sys.exit(result.returncode)


def create_env():
    venv_path = Path(VENV_DIR)
    if venv_path.exists():
        logger.error(
            f"Environment directory {VENV_DIR} already exists. " "Remove it first to create a fresh environment."
        )
        sys.exit(1)

    logger.info("Creating new virtual environment...")
    venv.create(venv_path, with_pip=True)

    python = get_python(True)
    logger.info(f"Using Python: {python}")

    run([python, "-m", "pip", "install", "--upgrade", "pip"], use_venv=True)
    run([python, "-m", "pip", "install", "-e", ".[test,dev]"], use_venv=True)
    logger.info("Environment created successfully")


def check(use_venv: bool):
    logger.info("Running type checks...")
    run(
        ["python3", "-m", "mypy", "--no-color-output", PACKAGE_NAME, TEST_DIR],
        use_venv=use_venv,
    )


def lint(use_venv: bool):
    logger.info("Running linters...")
    run(["python3", "-m", "ruff", "check", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)
    run(["python3", "-m", "pylint", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)


def fmt(use_venv: bool):
    logger.info("Formatting code...")
    run(["python3", "-m", "ruff", "check", "--select", "I", "--fix", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)
    run(["python3", "-m", "ruff", "format", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)


def test(use_venv: bool, with_coverage: bool = False):
    logger.info("Running tests...")

    unittest_cmd = ["python3", "-m", "unittest", "discover", "-v", "-s", TEST_DIR]
    cram_cmd = ["python3", "-m", "cram", TEST_DIR]
    extra_env: Optional[dict[str, str]] = None

    if with_coverage:
        config_file = Path("pyproject.toml").resolve()
        # Both the parent and the processes cram spawns must agree on where to
        # write, and the latter run with the cram scratch directory as their cwd.
        extra_env = {
            "COVERAGE_FILE": str(Path(".coverage").resolve()),
            "COVERAGE_PROCESS_START": str(config_file),
        }
        unittest_cmd = ["python3", "-m", "coverage", "run", "-m"] + unittest_cmd[2:]
        for stale in Path().glob(".coverage*"):
            stale.unlink()

    run(unittest_cmd, use_venv=use_venv, extra_env=extra_env)
    run(cram_cmd, use_venv=use_venv, extra_env=extra_env)

    if with_coverage:
        run(["python3", "-m", "coverage", "combine"], use_venv=use_venv, extra_env=extra_env)
        run(["python3", "-m", "coverage", "report"], use_venv=use_venv, extra_env=extra_env)


def main():
    parser = argparse.ArgumentParser(description="Ananke task automation")
    parser.add_argument("-e", "--venv", action="store_true", help="Use virtual environment")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(Command.CREATE_ENV.value, help="Create a new virtual environment")
    subparsers.add_parser(Command.CHECK.value, help="Run type checks")
    subparsers.add_parser(Command.LINT.value, help="Run linters")
    subparsers.add_parser(Command.FMT.value, help="Format code")
    test_parser = subparsers.add_parser(Command.TEST.value, help="Run tests")
    test_parser.add_argument("-c", "--coverage", action="store_true", help="Measure coverage")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    command = Command(args.command)

    match command:
        case Command.CREATE_ENV:
            create_env()
        case Command.CHECK:
            check(args.venv)
        case Command.LINT:
            lint(args.venv)
        case Command.FMT:
            fmt(args.venv)
        case Command.TEST:
            test(args.venv, args.coverage)


if __name__ == "__main__":
    main()
