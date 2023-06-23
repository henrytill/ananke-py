"""The command line interface."""
import argparse
import os
from typing import Mapping, Tuple

from . import config, version
from .app import Application
from .codec import GpgCodec
from .config import Backend, ConfigBuilder, OsFamily
from .data import Description, Entry, EntryId, Identity, Plaintext
from .store import InMemoryStore, JsonFileReader, JsonFileWriter


def get_version() -> str:
    """Returns the version of the application."""
    return version.__version__


def setup_application(host_os: OsFamily, env: Mapping[str, str]) -> Application:
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

    if cfg.backend is Backend.JSON:
        store = InMemoryStore()
        reader = JsonFileReader(cfg.data_file)
        writer = JsonFileWriter(cfg.data_file)
    else:
        raise NotImplementedError(f'Backend {cfg.backend} is not supported')

    codec = GpgCodec(cfg.key_id)
    return Application(store, reader, writer, codec)


def handle_add(args: argparse.Namespace) -> int:
    """Handles the 'add' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    os_family = OsFamily.from_str(os.name)
    with setup_application(os_family, os.environ) as app:
        user_plaintext = Plaintext(input('Enter plaintext: '))
        app.add(args.description, user_plaintext, args.identity, args.meta)
    return 0


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


def handle_modify(args: argparse.Namespace) -> int:
    """Handles the 'modify' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    os_family = OsFamily.from_str(os.name)
    with setup_application(os_family, os.environ) as app:
        target = args.description if args.description is not None else args.entry_id
        maybe_plaintext = Plaintext(input('Enter plaintext: ')) if args.plaintext else None
        app.modify(target, None, args.identity, maybe_plaintext, args.meta)
    return 0


def handle_remove(args: argparse.Namespace) -> int:
    """Handles the 'remove' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    os_family = OsFamily.from_str(os.name)
    with setup_application(os_family, os.environ) as app:
        target = args.description if args.description is not None else args.entry_id
        app.remove(target)
    return 0


def main() -> int:
    """The main entry point of the application.

    This function parses the command line arguments and calls the appropriate
    function.

    Returns:
        The exit code of the application.
    """
    parser = argparse.ArgumentParser(description='A minimal password manager.')
    parser.add_argument('--version', action='version', version=f'%(prog)s {get_version()}')
    subparsers = parser.add_subparsers(help='Commands')

    parser_add = subparsers.add_parser('add', help='add an entry')
    parser_add.add_argument('description', type=Description, help='URL or description')
    parser_add.add_argument('-i', '--identity', type=Identity, help='username or email address')
    parser_add.add_argument('-m', '--meta', type=str, help='additional metadata')
    parser_add.set_defaults(func=handle_add)

    parser_lookup = subparsers.add_parser('lookup', help='lookup an entry')
    parser_lookup.add_argument('description', type=Description, help='URL or description')
    parser_lookup.add_argument('-i', '--identity', type=Identity, help='username or email address')
    parser_lookup.add_argument('-v', '--verbose', action='store_true', help='enable verbose output')
    parser_lookup.set_defaults(func=handle_lookup)

    parser_modify = subparsers.add_parser('modify', help='modify an entry')
    parser_modify_group = parser_modify.add_mutually_exclusive_group(required=True)
    parser_modify_group.add_argument('-d', '--description', type=Description, help='URL or description')
    parser_modify_group.add_argument('-e', '--entry-id', type=EntryId, help='entry ID')
    parser_modify.add_argument('-i', '--identity', type=Identity, help='username or email address')
    parser_modify.add_argument('-m', '--meta', type=str, help='additional metadata')
    parser_modify.add_argument('-p', '--plaintext', action='store_true', help='modify plaintext')
    parser_modify.set_defaults(func=handle_modify)

    parser_remove = subparsers.add_parser('remove', help='remove an entry')
    parser_remove_group = parser_remove.add_mutually_exclusive_group(required=True)
    parser_remove_group.add_argument('-d', '--description', type=Description, help='URL or description')
    parser_remove_group.add_argument('-e', '--entry-id', type=EntryId, help='entry ID')
    parser_remove.set_defaults(func=handle_remove)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 2

    ret: int = args.func(args)

    return ret
