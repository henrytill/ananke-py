"""The command line interface."""
import argparse
import json
import os
from enum import Enum
from typing import Optional

from .codec import GpgCodec
from .config import Config, ConfigBuilder, OsFamily
from .data import Description, Entry, Identity, Plaintext
from .store import InMemoryStore, Query


class Verbosity(Enum):
    """Represents the verbosity level of the output."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


def lookup(
    config: Config,
    description: Description,
    maybe_identity: Optional[Identity] = None,
    verbosity: Verbosity = Verbosity.MEDIUM,
) -> list[Plaintext]:
    """Searches for entries that match the provided description and identity, and
    returns the plaintexts of the matching entries.

    Args:
        description: The description to search for.
        maybe_identity: The identity to search for.
        verbosity: The verbosity level of the output.

    Returns:
        A list of plaintexts that match the provided description and identity.
    """
    del verbosity  # Unused.

    with open(config.data_file, 'r', encoding='utf-8') as file:
        data = file.read()

    entries: list[Entry] = [Entry.from_dict(entry) for entry in json.loads(data)]

    store = InMemoryStore.from_entries(entries)

    codec = GpgCodec(config.key_id)

    query = Query(description=description, identity=maybe_identity)

    return [codec.decode(result.ciphertext) for result in store.query(query)]


def handle_lookup(args: argparse.Namespace) -> int:
    """Handles the 'lookup' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    description: Description = args.description
    maybe_identity: Optional[Identity] = args.identity
    verbosity: Verbosity = args.verbosity

    env = os.environ
    host_os = OsFamily.from_str(os.name)
    config = ConfigBuilder().with_defaults(host_os, env).with_env(env).build()

    for plaintext in lookup(config, description, maybe_identity, verbosity):
        print(plaintext)

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
    parser_lookup.add_argument('description', type=Description)
    parser_lookup.add_argument('--identity', type=Identity)
    parser_lookup.add_argument('--verbosity', default=1, type=Verbosity)
    parser_lookup.set_defaults(func=handle_lookup)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 2

    ret: int = args.func(args)

    return ret
