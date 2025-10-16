#!/usr/bin/env python3

import argparse
import logging
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


class CommandType(Enum):
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


def run(cmd: list[str], use_venv: bool = False):
    python = get_python(use_venv)
    if cmd[0] in ("python3", "python"):
        cmd[0] = python
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


def generate(git_ref: Optional[str] = None):
    base_version = "0.1.0"
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
    run([python, "-m", "pip", "install", "-e", ".[types,test,dev]"], use_venv=True)
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


def test(use_venv: bool):
    logger.info("Running tests...")
    run(
        ["python3", "-m", "unittest", "discover", "-v", "-s", TEST_DIR],
        use_venv=use_venv,
    )
    run(["python3", "-m", "cram", "tests"], use_venv=use_venv)


def main():
    parser = argparse.ArgumentParser(description="Ananke task automation")
    parser.add_argument("-e", "--venv", action="store_true", help="Use virtual environment")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(CommandType.GENERATE.value, help="Generate version file")
    gen_parser.add_argument("-g", "--git-ref", help="Git reference for version")

    subparsers.add_parser(CommandType.CREATE_ENV.value, help="Create a new virtual environment")
    subparsers.add_parser(CommandType.CHECK.value, help="Run type checks")
    subparsers.add_parser(CommandType.LINT.value, help="Run linters")
    subparsers.add_parser(CommandType.FMT.value, help="Format code")
    subparsers.add_parser(CommandType.TEST.value, help="Run tests")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    command = CommandType(args.command)

    match command:
        case CommandType.GENERATE:
            generate(args.git_ref)
        case CommandType.CREATE_ENV:
            create_env()
        case CommandType.CHECK:
            check(args.venv)
        case CommandType.LINT:
            lint(args.venv)
        case CommandType.FMT:
            fmt(args.venv)
        case CommandType.TEST:
            test(args.venv)


if __name__ == "__main__":
    main()
