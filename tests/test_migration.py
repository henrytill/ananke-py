"""Tests for migration functionality."""

import json
import shutil
import sqlite3
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from ananke.cli import migrate
from ananke.config import ConfigBuilder, Env, OsFamily
from ananke.data.migration import MigrationError
from ananke.data.schema import CURRENT_SCHEMA_VERSION, SchemaVersion, get_schema_version

UNKNOWN_SCHEMA_VERSION = SchemaVersion(2**63 - 1)  # Equivalent to u64::MAX


def create_schema_file(data_dir: Path, version: int) -> None:
    """Create a schema file with the specified version."""
    schema_file = data_dir / "db" / "schema"
    schema_file.parent.mkdir(parents=True, exist_ok=True)
    schema_file.write_text(str(version), encoding="utf-8")


def check_schema(data_dir: Path, expected_version: int) -> None:
    """Check that the schema file contains the expected version."""
    schema_file = data_dir / "db" / "schema"
    actual_version = get_schema_version(schema_file)
    assert actual_version == SchemaVersion(
        expected_version
    ), f"Expected schema version {expected_version}, got {actual_version}"


class TestJsonMigration(unittest.TestCase):
    """Test JSON migration functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        # pylint: disable=consider-using-with
        self.temp_dir = TemporaryDirectory(prefix="ananke-migration-test-")
        self.data_dir = Path(self.temp_dir.name)
        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: "json",
            Env.KEY_ID: "371C136C",
            Env.ALLOW_MULTIPLE_KEYS: "false",
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()

    def tearDown(self) -> None:
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def _copy_json_data(self, source_file: str) -> None:
        """Copy JSON test data to target location."""
        source_path = Path("tests/migration_data") / source_file
        target_file = self.data_dir / "db" / "data.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source_path, target_file)

    def test_migrate_v2_v4(self) -> None:
        """Test migration from schema v2 to v4."""
        self._copy_json_data("data-schema-v2.json")
        create_schema_file(self.data_dir, 2)

        migrate(self.config, SchemaVersion(2))

        self.config.schema_file.write_text(str(CURRENT_SCHEMA_VERSION), encoding="utf-8")

        check_schema(self.data_dir, 4)

        with open(self.config.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Should have camelCase fields (v2->v3) and UUID IDs (v3->v4)
        for entry in data:
            self.assertIn("timestamp", entry)
            self.assertIn("id", entry)
            self.assertIn("keyId", entry)
            self.assertIn("description", entry)
            self.assertIn("ciphertext", entry)

            # Old PascalCase fields should be gone
            self.assertNotIn("Timestamp", entry)
            self.assertNotIn("Id", entry)
            self.assertNotIn("KeyId", entry)
            self.assertNotIn("Description", entry)
            self.assertNotIn("Identity", entry)
            self.assertNotIn("Ciphertext", entry)
            self.assertNotIn("Meta", entry)

            uuid.UUID(entry["id"])

    def test_migrate_v3_v4(self) -> None:
        """Test migration from schema v3 to v4."""
        self._copy_json_data("data-schema-v3.json")
        create_schema_file(self.data_dir, 3)

        migrate(self.config, SchemaVersion(3))

        self.config.schema_file.write_text(str(CURRENT_SCHEMA_VERSION), encoding="utf-8")

        check_schema(self.data_dir, 4)

        with open(self.config.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Should have UUID IDs (v3->v4)
        for entry in data:
            uuid.UUID(entry["id"])

    def test_migrate_to_unknown_schema_version(self) -> None:
        """Test migration to unknown schema version."""
        self._copy_json_data("data-schema-v2.json")
        create_schema_file(self.data_dir, UNKNOWN_SCHEMA_VERSION.value)

        with self.assertRaises(MigrationError) as cm:
            migrate(self.config, UNKNOWN_SCHEMA_VERSION)

        self.assertIn("no supported migration path", str(cm.exception))


class TestSqliteMigration(unittest.TestCase):
    """Test SQLite migration functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        # pylint: disable=consider-using-with
        self.temp_dir = TemporaryDirectory(prefix="ananke-migration-test-")
        self.data_dir = Path(self.temp_dir.name)
        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: "sqlite",
            Env.KEY_ID: "371C136C",
            Env.ALLOW_MULTIPLE_KEYS: "false",
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()

    def tearDown(self) -> None:
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def _copy_sqlite_data(self, source_file: str) -> None:
        """Copy SQLite test data by executing SQL script."""
        source_path = Path("tests/migration_data") / source_file
        target_file = self.data_dir / "db" / "db.sqlite"
        target_file.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(target_file) as conn:
            sql_script = source_path.read_text(encoding="utf-8")
            conn.executescript(sql_script)
            conn.commit()

    def test_migrate_v1_v4(self) -> None:
        """Test migration from schema v1 to v4 ."""
        self._copy_sqlite_data("data-schema-v1.sql")
        create_schema_file(self.data_dir, 1)

        migrate(self.config, SchemaVersion(1))

        self.config.schema_file.write_text(str(CURRENT_SCHEMA_VERSION), encoding="utf-8")

        check_schema(self.data_dir, 4)

        with sqlite3.connect(self.config.data_file) as conn:
            # Should have keyid column added (v1->v2)
            cursor = conn.execute("SELECT keyid FROM entries LIMIT 1")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "371C136C")

            # Should have UUID IDs (v3->v4)
            cursor = conn.execute("SELECT id FROM entries")
            for (entry_id,) in cursor.fetchall():
                uuid.UUID(entry_id)

    def test_migrate_v2_v4(self) -> None:
        """Test migration from schema v2 to v4 ."""
        self._copy_sqlite_data("data-schema-v2.sql")
        create_schema_file(self.data_dir, 2)

        migrate(self.config, SchemaVersion(2))

        self.config.schema_file.write_text(str(CURRENT_SCHEMA_VERSION), encoding="utf-8")

        check_schema(self.data_dir, 4)

        with sqlite3.connect(self.config.data_file) as conn:
            # Should have UUID IDs (v3->v4)
            cursor = conn.execute("SELECT id FROM entries")
            for (entry_id,) in cursor.fetchall():
                uuid.UUID(entry_id)

    def test_migrate_to_unknown_schema_version(self) -> None:
        """Test migration to unknown schema version ."""
        self._copy_sqlite_data("data-schema-v2.sql")
        create_schema_file(self.data_dir, UNKNOWN_SCHEMA_VERSION.value)

        with self.assertRaises(MigrationError) as cm:
            migrate(self.config, UNKNOWN_SCHEMA_VERSION)

        self.assertIn("no supported migration path", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
