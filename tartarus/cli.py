import argparse
from enum import Enum

from . import gpg
from .config import ConfigBuilder
from .data import Entries


class Verbosity(Enum):
    """
    Represents the verbosity level of the output.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3


def lookup(args: argparse.Namespace):
    """
    Searches for an 'Entry' that matches the provided description.

    Args:
        args: The arguments provided by the user.
    """
    config = ConfigBuilder().with_env().with_defaults().build()

    with open(config.data_file, 'r') as f:
        data = f.read()
        entries = Entries.from_json(data)

    results = entries.lookup(args.description, args.identity)

    for r in results:
        plaintext = gpg.decrypt(r.ciphertext)
        print(plaintext)


def main() -> int:
    """
    The main entry point of the application.

    This function parses the command line arguments and calls the appropriate function.

    Returns:
        The exit code of the application.
    """
    parser = argparse.ArgumentParser(description='A minimal password manager.')
    subparsers = parser.add_subparsers(help='Commands')

    parser_lookup = subparsers.add_parser('lookup')
    parser_lookup.add_argument('description')
    parser_lookup.add_argument('--identity')
    parser_lookup.add_argument('--verbosity', default=1, type=Verbosity)
    parser_lookup.set_defaults(func=lookup)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    args.func(args)

    return 0
