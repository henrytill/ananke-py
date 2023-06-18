"""The command line interface."""
import argparse
import os
from typing import Mapping, Tuple

from . import config
from .app import Application
from .codec import GpgCodec
from .config import Backend, ConfigBuilder, OsFamily
from .data import Description, Entry, Identity, Plaintext
from .store import InMemoryStore, JsonFileReader, JsonFileWriter


def setup_application(
    host_os: OsFamily,
    env: Mapping[str, str],
) -> 'Application':
    """Sets up the application with necessary dependencies.

    This includes setting up an in-memory store, creating a configuration object
    using environment variables, initializing file reader and writer, and
    setting up a GPG codec for encryption and decryption.

    Args:
        host_os: The host operating system, defaulting to the current OS.
        env: The environment variables to be used for configuration.

    Returns:
        The configured Application instance ready for use.
    """
    config_file = config.get_config_file(host_os, env)

    with open(config_file, encoding='ascii') as file:
        config_str = file.read()

    cfg = ConfigBuilder().with_defaults(host_os, env).with_config(config_str).with_env(env).build()

    if cfg.backend == Backend.JSON:
        store = InMemoryStore()
        reader = JsonFileReader(cfg.data_file)
        writer = JsonFileWriter(cfg.data_file)
    else:
        raise NotImplementedError(f'Backend {cfg.backend} is not supported')

    codec = GpgCodec(cfg.key_id)
    return Application(store, reader, writer, codec)


def format_verbose(entry: Entry, plaintext: Plaintext) -> str:
    """Formats an entry in verbose mode.

    Args:
        entry: The entry to format.
        plaintext: The plaintext to format.

    Returns:
        The formatted entry.
    """
    elements = [entry.timestamp.isoformat(), entry.entry_id, entry.key_id, entry.description]

    if entry.identity is not None:
        elements.append(entry.identity)

    elements.append(plaintext)

    if entry.meta is not None:
        elements.append(f'"{entry.meta}"')

    return ' '.join(elements)


def format_results(results: list[Tuple[Entry, Plaintext]], verbose: bool) -> str:
    """Formats the results of a lookup.

    Args:
        results: The results to format.
        verbose: Whether to format the results in verbose mode.

    Returns:
        The formatted results.
    """
    if len(results) == 1:
        entry, plaintext = results[0]
        return format_verbose(entry, plaintext) if verbose else plaintext

    formatted_results: list[str] = []
    for entry, plaintext in results:
        formatted = format_verbose(entry, plaintext) if verbose else f'{entry.description} {entry.identity} {plaintext}'
        formatted_results.append(formatted)
    return '\n'.join(formatted_results)


def handle_lookup(args: argparse.Namespace) -> int:
    """Handles the 'lookup' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    os_family = OsFamily.from_str(os.name)
    with setup_application(os_family, os.environ) as app:
        results = app.lookup(args.description, args.identity)
        print(format_results(results, args.verbose))
    return 0


def main() -> int:
    """The main entry point of the application.

    This function parses the command line arguments and calls the appropriate
    function.

    Returns:
        The exit code of the application.
    """
    parser = argparse.ArgumentParser(description='A minimal password manager.')
    subparsers = parser.add_subparsers(help='Commands')

    parser_lookup = subparsers.add_parser('lookup')
    parser_lookup.add_argument('description', type=Description, help='URL or description')
    parser_lookup.add_argument('-i', '--identity', type=Identity, help='username or email address')
    parser_lookup.add_argument('-v', '--verbose', action='store_true', help='enable verbose output')
    parser_lookup.set_defaults(func=handle_lookup)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 2

    ret: int = args.func(args)

    return ret
