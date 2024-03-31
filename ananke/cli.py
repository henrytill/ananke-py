"""The command line interface."""

import argparse
import os
from pathlib import Path
from typing import Mapping, Tuple

from . import data, version
from .app import Application
from .config import Backend, Config, ConfigBuilder, OsFamily
from .data import CURRENT_SCHEMA_VERSION, Description, Entry, EntryId, GpgCodec, Identity, Plaintext, SchemaVersion
from .store import InMemoryStore, JsonFileReader, JsonFileWriter, NoOpWriter, SqliteConnectionReader, SqliteStore


def get_version() -> str:
    """Returns the version of the application."""
    return version.__version__


def migrate(cfg: Config, found: SchemaVersion) -> None:
    """Migrates the data to the current schema version.

    Args:
        cfg: The configuration.
        found: The schema version found in the schema file.
    """
    raise NotImplementedError()


def application(host_os: OsFamily, env: Mapping[str, str]) -> Application:
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
    cfg = ConfigBuilder().with_defaults(host_os, env).with_config().with_env(env).build()

    dir_mode = 0o700
    if not cfg.config_dir.exists():
        cfg.config_dir.mkdir(mode=dir_mode)
    if not cfg.data_dir.exists():
        cfg.db_dir.mkdir(mode=dir_mode)
    if not cfg.db_dir.exists():
        cfg.db_dir.mkdir(mode=dir_mode)

    schema_version = data.get_schema_version(cfg.schema_file)
    if schema_version < CURRENT_SCHEMA_VERSION:
        migrate(cfg, schema_version)
    elif schema_version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(f"Schema version {schema_version} is not supported")

    match cfg.backend:
        case Backend.JSON:
            return Application(
                store=InMemoryStore(),
                reader=JsonFileReader(cfg.data_file),
                writer=JsonFileWriter(cfg.data_file),
                codec=GpgCodec(cfg.key_id),
            )
        case Backend.SQLITE:
            return Application(
                store=SqliteStore(),
                reader=SqliteConnectionReader(cfg.data_file),
                writer=NoOpWriter(),
                codec=GpgCodec(cfg.key_id),
            )


def handle_add(args: argparse.Namespace) -> int:
    """Handles the 'add' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    os_family = OsFamily.from_str(os.name)
    with application(os_family, os.environ) as app:
        user_plaintext = Plaintext(input("Enter plaintext: "))
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
    elements = [entry.timestamp.isoformat(), str(entry.entry_id), entry.key_id, entry.description]

    if entry.identity is not None:
        elements.append(entry.identity)

    elements.append(str(plaintext))

    if entry.meta is not None:
        elements.append(f'"{entry.meta}"')

    return " ".join(elements)


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
        return format_verbose(entry, plaintext) if verbose else str(plaintext)

    formatted_results: list[str] = []
    for entry, plaintext in results:
        formatted = format_verbose(entry, plaintext) if verbose else f"{entry.description} {entry.identity} {plaintext}"
        formatted_results.append(formatted)
    return "\n".join(formatted_results)


def handle_lookup(args: argparse.Namespace) -> int:
    """Handles the 'lookup' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    os_family = OsFamily.from_str(os.name)
    results = []
    with application(os_family, os.environ) as app:
        results = app.lookup(args.description, args.identity)
    if not results:
        return 1
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
    with application(os_family, os.environ) as app:
        target = args.description if args.description is not None else args.entry_id
        maybe_plaintext = Plaintext(input("Enter plaintext: ")) if args.plaintext else None
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
    with application(os_family, os.environ) as app:
        target = args.description if args.description is not None else args.entry_id
        app.remove(target)
    return 0


def handle_import(args: argparse.Namespace) -> int:
    """Handles the 'import' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    file_path = args.file
    if not isinstance(file_path, Path):
        raise TypeError("Expected Path")
    reader = JsonFileReader(file_path)
    entries: list[Entry] = reader.read()
    os_family = OsFamily.from_str(os.name)
    with application(os_family, os.environ) as app:
        for entry in entries:
            app.store.put(entry)
    return 0


def handle_export(args: argparse.Namespace) -> int:
    """Handles the 'export' command.

    Args:
        args: The command line arguments.

    Returns:
        The exit code of the application.
    """
    file_path = args.file
    if not isinstance(file_path, Path):
        raise TypeError("Expected Path")
    os_family = OsFamily.from_str(os.name)
    with application(os_family, os.environ) as app:
        entries = app.dump()
    writer = JsonFileWriter(file_path)
    writer.write(entries)
    return 0


def main() -> int:
    """The main entry point for the command-line interface.

    Returns:
        An exit code.
    """
    parser = argparse.ArgumentParser(description="A minimal password manager.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {get_version()}")
    subparsers = parser.add_subparsers(help="Commands")

    parser_add = subparsers.add_parser("add", help="add an entry")
    parser_add.add_argument("description", type=Description, help="URL or description")
    parser_add.add_argument("-i", "--identity", type=Identity, help="username or email address")
    parser_add.add_argument("-m", "--meta", type=str, help="additional metadata")
    parser_add.set_defaults(func=handle_add)

    parser_lookup = subparsers.add_parser("lookup", help="lookup an entry")
    parser_lookup.add_argument("description", type=Description, help="URL or description")
    parser_lookup.add_argument("-i", "--identity", type=Identity, help="username or email address")
    parser_lookup.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")
    parser_lookup.set_defaults(func=handle_lookup)

    parser_modify = subparsers.add_parser("modify", help="modify an entry")
    parser_modify_group = parser_modify.add_mutually_exclusive_group(required=True)
    parser_modify_group.add_argument("-d", "--description", type=Description, help="URL or description")
    parser_modify_group.add_argument("-e", "--entry-id", type=EntryId, help="entry ID")
    parser_modify.add_argument("-p", "--plaintext", action="store_true", help="modify plaintext")
    parser_modify.add_argument("-i", "--identity", type=Identity, help="username or email address")
    parser_modify.add_argument("-m", "--meta", type=str, help="additional metadata")
    parser_modify.set_defaults(func=handle_modify)

    parser_remove = subparsers.add_parser("remove", help="remove an entry")
    parser_remove_group = parser_remove.add_mutually_exclusive_group(required=True)
    parser_remove_group.add_argument("-d", "--description", type=Description, help="URL or description")
    parser_remove_group.add_argument("-e", "--entry-id", type=EntryId, help="entry ID")
    parser_remove.set_defaults(func=handle_remove)

    parser_import = subparsers.add_parser("import", help="import entries from JSON file")
    parser_import.add_argument("file", type=Path, help="file to import from")
    parser_import.set_defaults(func=handle_import)

    parser_export = subparsers.add_parser("export", help="export entries to JSON file")
    parser_export.add_argument("file", type=Path, help="file to export to")
    parser_export.set_defaults(func=handle_export)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    ret = args.func(args)
    if not isinstance(ret, int):
        raise TypeError("Expected int")

    return ret
