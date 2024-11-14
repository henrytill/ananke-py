#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

PYTHON=python3
MYPY=mypy
VENV=env

USE_VENV=0
VERBOSE=0

generate() {
    local version="0.1.0"

    if [ -n "$(command -v git)" -a -z "${1+x}" ]; then
        local git_ref=$(git rev-parse --short HEAD)
        version="${version}+${git_ref}"
    elif [ -n "${1+x}" ]; then
        version="${version}+${1}"
    fi

    if [ $VERBOSE -eq 1 ]; then
        printf "version=%s\n" $version
    fi

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
    generate
    $PYTHON -m venv $VENV
    activate
    which $PYTHON
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -e .[test,dev]
}

check() {
    activate
    $MYPY --no-color-output ananke
    $MYPY --no-color-output tests
}

lint() {
    activate
    $PYTHON -m flake8 --config .flake8
    $PYTHON -m pylint ananke tests
}

fmt() {
    activate
    $PYTHON -m isort ananke tests
    $PYTHON -m black ananke tests
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
        fmt)
            fmt
            ;;
        test)
            test
            ;;
    esac

    exit 0
}

while getopts "ev" name; do
    case $name in
        e)
            USE_VENV=1
            ;;
        v)
            VERBOSE=1
            ;;
    esac
done

shift $(($OPTIND - 1))

unset name
unset OPTIND

if [ $VERBOSE -eq 1 ]; then
    printf "USE_VENV=%d\n" $USE_VENV
fi

if [ $# -eq 0 ]; then
    action default
else
    action $*
fi
