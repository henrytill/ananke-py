#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

PYTHON=python3
MYPY=mypy
VENV=env

USE_VENV=0

generate() {
    local version="0.1.0"

    if [ -n "$(command -v git)" -a -z "${1+x}" ]; then
        local git_ref=$(git rev-parse --short HEAD)
        version="${version}+${git_ref}"
    elif [ -n "$1" ]; then
        version="${version}+${1}"
    fi

    printf "version: %s\n" $version

    cat <<EOF >ananke/version.py
"""This module contains version information."""

# This file is auto-generated, do not edit by hand
__version__ = "$version"
EOF
}

activate() {
    if [ $USE_VENV -eq 1 ]; then
        source "${VENV}/bin/activate"
    fi
}

create_env() {
    USE_VENV=1
    $PYTHON -m venv $VENV
    activate
    which $PYTHON
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -e .[test,dev]
}

check() {
    activate
    $MYPY ananke
    $MYPY tests
}

lint() {
    activate
    $PYTHON -m flake8 --config .flake8
    $PYTHON -m pylint ananke tests
}

test() {
    activate
    $PYTHON -m unittest discover -v -s tests
    $PYTHON -m doctest -v ananke/data/common.py
    $PYTHON -m cram tests
}

action() {
    subcommand=$1
    shift

    case $subcommand in
        default)
            printf "Hello, world!\n"
            ;;
        generate)
            local git_ref=
            while getopts "g:" name; do
                case $name in
                    g)
                        git_ref="$OPTARG"
                        ;;
                esac
            done
            generate $git_ref
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
        test)
            test
            ;;
    esac

    exit 0
}

while getopts "e" name; do
    case $name in
        e)
            USE_VENV=1
            ;;
    esac
done

shift $(($OPTIND - 1))

unset name
unset OPTIND

printf "USE_VENV=%d\n" $USE_VENV

if [ $# -eq 0 ]; then
    action default
else
    action $*
fi
