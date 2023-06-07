import argparse
import os
from enum import Enum
from pathlib import Path

import tartarus.gpg as gpg
from tartarus.data import Entries


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
    data_dir = os.getenv('HECATE_DATA_DIR')
    if data_dir is None:
        config_home: Path = os.getenv('XDG_CONFIG_HOME') or '~/.config'
        data_dir = os.path.join(config_home, 'hecate')
        data_file = os.path.join(data_dir, 'db', 'data.json')
    else:
        data_file = os.path.join(data_dir, 'db', 'data.json')
    # Parse the data file
    with open(data_file, 'r') as f:
        data = f.read()
        entries = Entries.from_json(data)
    # Lookup the entry
    entry = entries.lookup(args.description, args.identity)
    # Print the entry
    for e in entry:
        ciphertext = e.ciphertext
        plaintext = gpg.decrypt(ciphertext)
        print(plaintext)


def main():
    parser = argparse.ArgumentParser(description='A minimal password manager.')
    subparsers = parser.add_subparsers(help='Commands')

    parser_lookup = subparsers.add_parser('lookup')
    parser_lookup.add_argument('description')
    parser_lookup.add_argument('--identity')
    parser_lookup.add_argument('--verbosity', default=1, type=Verbosity)
    parser_lookup.set_defaults(func=lookup)

    args = parser.parse_args()

    # Call the appropriate function based on the provided command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
