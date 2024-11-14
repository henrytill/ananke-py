#!/usr/bin/env bash

# Exit on error, undefined vars, and pipe failures
set -o errexit
set -o nounset
set -o pipefail

# Configuration variables
readonly PYTHON=python3
readonly MYPY=mypy
readonly VENV=env
readonly PACKAGE_NAME="ananke"
readonly TEST_DIR="tests"

# Default values for command line options
USE_VENV=0
VERBOSE=0

log() {
    if [ $VERBOSE -eq 1 ]; then
        printf "[INFO] %s\n" "$1"
    fi
}

error() {
    printf "[ERROR] %s\n" "$1" >&2
    exit 1
}

generate_version() {
    local base_version="0.1.0"
    local version="${base_version}"
    local git_ref="${1:-}"

    if [ -z "$git_ref" ] && command -v git >/dev/null; then
        git_ref=$(git rev-parse --short HEAD 2>/dev/null || true)
    fi

    if [ -n "$git_ref" ]; then
        version="${base_version}+${git_ref}"
    fi

    log "Generated version: ${version}"

    cat <<EOF >"${PACKAGE_NAME}/version.py"
"""This module contains version information."""

# This file is auto-generated, do not edit by hand
__version__ = "${version}"
EOF
}

activate_venv() {
    local flag=${1:-0}
    if [ $USE_VENV -eq 1 -o $flag -eq 1 ]; then
        if [ ! -f "${VENV}/bin/activate" ]; then
            error "Virtual environment not found. Run './build.sh create-env' first"
        fi
        source "${VENV}/bin/activate"
        log "Activated virtual environment at ${VENV}"
    fi
}

create_env() {
    if [ -d "$VENV" ]; then
        error "Environment directory ${VENV} already exists. Remove it first to create a fresh environment."
    fi

    log "Creating new virtual environment..."
    generate_version
    $PYTHON -m venv "$VENV"
    activate_venv 1
    log "Using Python: $(which $PYTHON)"
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -e ".[types,test,dev]"
    log "Environment created successfully"
}

check() {
    log "Running type checks..."
    activate_venv
    $MYPY --no-color-output "$PACKAGE_NAME" "$TEST_DIR"
}

lint() {
    log "Running linters..."
    activate_venv
    $PYTHON -m flake8 --config .flake8
    $PYTHON -m pylint "$PACKAGE_NAME" "$TEST_DIR"
}

format() {
    log "Formatting code..."
    activate_venv
    $PYTHON -m isort "$PACKAGE_NAME" "$TEST_DIR"
    $PYTHON -m black "$PACKAGE_NAME" "$TEST_DIR"
}

run_tests() {
    log "Running tests..."
    activate_venv
    $PYTHON -m unittest discover -v -s "$TEST_DIR"
    $PYTHON -m doctest -v ananke/data/common.py
    $PYTHON -m cram tests
}

usage() {
    cat >&2 <<EOF
Usage: $0 [-e] [-v] <command>

Options:
    -e          Use virtual environment
    -v          Verbose output

Commands:
    create-env  Create a new virtual environment
    generate    Generate version file
    check       Run type checks
    lint        Run linters
    fmt         Format code
    test        Run tests
EOF
    exit 1
}

main() {
    # Parse global options
    while getopts "ev" opt; do
        case $opt in
            e) USE_VENV=1 ;;
            v) VERBOSE=1 ;;
            *) usage ;;
        esac
    done
    shift $((OPTIND - 1))

    [ $# -eq 0 ] && usage

    local command=$1
    shift

    case $command in
        generate)
            local git_ref=""
            while getopts "g:" opt; do
                case $opt in
                    g) git_ref="$OPTARG" ;;
                    *) usage ;;
                esac
            done
            generate_version "$git_ref"
            ;;
        create-env)
            create_env
            ;;
        check)
            check
            ;;
        lint)
            lint
            ;;
        fmt)
            format
            ;;
        test)
            run_tests
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"
