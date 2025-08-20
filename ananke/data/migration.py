"""Migration functionality for ananke data formats."""

import functools
import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, cast

from ..config import Config
from . import common
from .schema import SchemaVersion


class MigrationError(Exception):
    """Exception raised during migration operations."""


def migrate_json_data(config: Config, from_version: SchemaVersion) -> None:
    """Migrate JSON data file from a specific schema version to current.

    Args:
        config: Configuration object containing paths and settings
        from_version: The schema version to migrate from

    Raises:
        MigrationError: If migration fails or unsupported version
    """
    data_file = config.data_file

    if not data_file.exists():
        return

    if from_version == SchemaVersion(3):
        _migrate_json_v3_to_v4(data_file)
    elif from_version == SchemaVersion(2):
        _migrate_json_v2_to_v3(data_file)
        _migrate_json_v3_to_v4(data_file)
    elif from_version == SchemaVersion(1):
        raise MigrationError("schema version 1 not supported by JSON backend")
    else:
        raise MigrationError(f"no supported migration path for schema version {from_version}")


def migrate_sqlite_data(config: Config, from_version: SchemaVersion) -> None:
    """Migrate SQLite data file from a specific schema version to current.

    Args:
        config: Configuration object containing paths and settings
        from_version: The schema version to migrate from

    Raises:
        MigrationError: If migration fails or unsupported version
    """
    data_file = config.data_file

    if not data_file.exists():
        return

    if from_version == SchemaVersion(3):
        _migrate_sqlite_v3_to_v4(data_file)
    elif from_version == SchemaVersion(2):
        _migrate_sqlite_v2_to_v3(data_file)
        _migrate_sqlite_v3_to_v4(data_file)
    elif from_version == SchemaVersion(1):
        _migrate_sqlite_v1_to_v2(data_file, config)
        _migrate_sqlite_v2_to_v3(data_file)
        _migrate_sqlite_v3_to_v4(data_file)
    else:
        raise MigrationError(f"no supported migration path for schema version {from_version}")


PASCAL_TO_CAMEL = {
    "Timestamp": "timestamp",
    "Id": "id",
    "KeyId": "keyId",
    "Description": "description",
    "Identity": "identity",
    "Ciphertext": "ciphertext",
    "Meta": "meta",
}

remap_keys_to_v3 = functools.partial(common.remap_keys, PASCAL_TO_CAMEL)


def _migrate_json_v2_to_v3(data_file: Path) -> None:
    """Migrate JSON data from schema v2 to v3 (field name changes)."""
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise MigrationError("JSON data is not an array")

    for entry in cast(List[object], data):
        if not isinstance(entry, dict):
            raise MigrationError("JSON entry is not an object")

        entry_dict = cast(Dict[str, Any], entry)
        remapped = remap_keys_to_v3(entry_dict)
        entry_dict.clear()
        entry_dict.update(remapped)

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.write("\n")


def _migrate_json_v3_to_v4(data_file: Path) -> None:
    """Migrate JSON data from schema v3 to v4 (add UUID-based IDs)."""
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise MigrationError("JSON data is not an array")

    for entry in cast(List[object], data):
        if not isinstance(entry, dict):
            raise MigrationError("JSON entry is not an object")
        entry["id"] = str(uuid.uuid4())

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.write("\n")


def _migrate_sqlite_v1_to_v2(data_file: Path, config: Config) -> None:
    """Migrate SQLite data from schema v1 to v2 (add keyid column)."""
    with sqlite3.connect(data_file) as conn:
        with closing(conn.cursor()) as cursor:
            alter_table_sql: str = """\
            ALTER TABLE entries RENAME TO entries_v1
            """

            create_table_sql: str = """\
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY NOT NULL,
                keyid TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                description TEXT NOT NULL,
                identity TEXT,
                ciphertext TEXT NOT NULL,
                meta TEXT
            )
            """

            insert_sql: str = """\
            INSERT INTO entries
            (id, keyid, timestamp, description, identity, ciphertext, meta)
            SELECT id, ?, timestamp, description, identity, ciphertext, meta
            FROM entries_v1
            """

            cursor.execute(alter_table_sql)
            cursor.execute(create_table_sql)
            cursor.execute(insert_sql, (config.key_id,))
            cursor.execute("DROP TABLE entries_v1")

        conn.commit()


def _migrate_sqlite_v2_to_v3(_data_file: Path) -> None:
    """Migrate SQLite data from schema v2 to v3 (no changes needed)."""


def _migrate_sqlite_v3_to_v4(data_file: Path) -> None:
    """Migrate SQLite data from schema v3 to v4 (replace hash IDs with UUIDs)."""
    with sqlite3.connect(data_file) as conn:
        with closing(conn.cursor()) as cursor:
            alter_table_sql: str = """\
            ALTER TABLE entries RENAME TO entries_v3
            """

            create_table_sql: str = """\
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY NOT NULL,
                keyid TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                description TEXT NOT NULL,
                identity TEXT,
                ciphertext TEXT NOT NULL,
                meta TEXT
            )
            """

            insert_sql: str = """\
            INSERT INTO entries
            (id, keyid, timestamp, description, identity, ciphertext, meta)
            SELECT id, keyid, timestamp, description, identity, ciphertext, meta
            FROM entries_v3
            """

            cursor.execute(alter_table_sql)
            cursor.execute(create_table_sql)
            cursor.execute(insert_sql)

            old_ids = cursor.execute("SELECT id FROM entries").fetchall()

            for (old_id,) in old_ids:
                new_id = str(uuid.uuid4())
                cursor.execute("UPDATE entries SET id = ? WHERE id = ?", (new_id, old_id))

            cursor.execute("DROP TABLE entries_v3")

        conn.commit()
