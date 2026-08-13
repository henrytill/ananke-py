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
VERSION_FILE = "VERSION"

logger = logging.getLogger(__name__)


class Command(Enum):
    GENERATE = "generate"
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


def generate(git_ref: Optional[str] = None):
    version_file = Path(VERSION_FILE)
    if not version_file.exists():
        logger.error(f"Version file {VERSION_FILE} not found")
        sys.exit(1)

    base_version = version_file.read_text().strip()
    version = base_version

    if git_ref is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                git_ref = result.stdout.strip()
        except FileNotFoundError:
            pass

    if git_ref:
        version = f"{base_version}+{git_ref}"

    logger.info(f"Generated version: {version}")

    init_file = Path(PACKAGE_NAME) / "__init__.py"
    init_file.write_text(
        f'''"""A password manager."""

# This file is auto-generated, do not edit by hand
__version__ = "{version}"
'''
    )


def create_env():
    venv_path = Path(VENV_DIR)
    if venv_path.exists():
        logger.error(
            f"Environment directory {VENV_DIR} already exists. " "Remove it first to create a fresh environment."
        )
        sys.exit(1)

    logger.info("Creating new virtual environment...")
    generate()
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
    run(["python3", "-m", "flake8", "--config", ".flake8"], use_venv=use_venv)
    run(["python3", "-m", "pylint", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)


def fmt(use_venv: bool):
    logger.info("Formatting code...")
    run(["python3", "-m", "isort", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)
    run(["python3", "-m", "black", PACKAGE_NAME, TEST_DIR], use_venv=use_venv)


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

    gen_parser = subparsers.add_parser(Command.GENERATE.value, help="Generate version file")
    gen_parser.add_argument("-g", "--git-ref", help="Git reference for version")

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
        case Command.GENERATE:
            generate(args.git_ref)
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
