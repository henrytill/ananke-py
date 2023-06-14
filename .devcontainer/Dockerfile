FROM mcr.microsoft.com/devcontainers/base:debian

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && \
        apt-get install -yqq black pylint python3-coverage python3-flake8 \
        python3-pip python3-venv
