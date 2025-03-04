"""Tests for the 'config' module."""

import textwrap
import unittest
from dataclasses import dataclass
from pathlib import Path

from ananke.cipher import KeyId
from ananke.config import Backend, ConfigBuilder, Env, OsFamily


# pylint: disable=too-few-public-methods
@dataclass(frozen=True)
class ConfigFile:
    """A configuration file."""

    BACKEND = "sqlite"
    DATA_DIR = "/tmp/data"
    KEY_ID = "alice_file@example.com"
    ALLOW_MULTIPLE_KEYS = "true"

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            [data]
            backend={self.BACKEND}
            dir={self.DATA_DIR}
            [gpg]
            key_id={self.KEY_ID}
            allow_multiple_keys={self.ALLOW_MULTIPLE_KEYS}
            """
        )


def config_reader(_config_path: Path) -> str:
    """A test configuration file reader."""
    return str(ConfigFile())


class TestOsFamily(unittest.TestCase):
    """Tests for the 'OsFamily' enum."""

    def test_from_str(self) -> None:
        """Tests the 'from_str' method."""
        self.assertEqual(OsFamily.from_str("posix"), OsFamily.POSIX)
        self.assertEqual(OsFamily.from_str("nt"), OsFamily.NT)

    def test_from_str_with_invalid_os(self) -> None:
        """Tests the 'from_str' method with an invalid OS."""
        self.assertRaises(ValueError, OsFamily.from_str, "invalid")

    def test_str(self) -> None:
        """Tests the '__str__' method."""
        self.assertEqual(str(OsFamily.POSIX), "posix")
        self.assertEqual(str(OsFamily.NT), "nt")


class TestBackend(unittest.TestCase):
    """Tests for the 'Backend' enum."""

    def test_from_str(self) -> None:
        """Tests the 'from_str' method."""
        self.assertEqual(Backend.from_str("json"), Backend.JSON)
        self.assertEqual(Backend.from_str("sqlite"), Backend.SQLITE)

    def test_from_str_with_invalid_backend(self) -> None:
        """Tests the 'from_str' method with an invalid backend."""
        self.assertRaises(ValueError, Backend.from_str, "invalid")


class TestConfigBuilder(unittest.TestCase):
    """Tests for the 'ConfigBuilder' class."""

    data_dir = Path("/foo/bar")
    key_id = KeyId("alice@example.com")

    def test_build(self) -> None:
        """Tests the 'build' method."""
        self.assertRaises(ValueError, ConfigBuilder().build)

    def test_build_with_defaults_posix(self) -> None:
        """Tests the 'build' method with POSIX defaults."""
        self.assertRaises(ValueError, ConfigBuilder().with_defaults(OsFamily.POSIX, {}).build)

    def test_build_with_defaults_nt(self) -> None:
        """Tests the 'build' method with NT defaults."""
        self.assertRaises(ValueError, ConfigBuilder().with_defaults(OsFamily.NT, {}).build)

    def test_build_without_data_dir(self) -> None:
        """Tests the 'build' method without a data directory."""
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                backend=Backend.SQLITE,
                key_id=self.key_id,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_key_id(self) -> None:
        """Tests the 'build' method without a key ID."""
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=self.data_dir,
                backend=Backend.SQLITE,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_backend(self) -> None:
        """Tests the 'build' method without a backend."""
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=self.data_dir,
                key_id=self.key_id,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_allow_multiple_keys(self) -> None:
        """Tests the 'build' method without allowing multiple keys."""
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=self.data_dir,
                backend=Backend.SQLITE,
                key_id=self.key_id,
            ).build,
        )

    def test_build_with_defaults_posix_env(self) -> None:
        """Tests the 'build' method with POSIX defaults and an environment."""
        env = {
            "XDG_DATA_HOME": str(self.data_dir),
        }

        test_config = ConfigBuilder(key_id=self.key_id, backend=Backend.JSON).with_defaults(OsFamily.POSIX, env).build()

        self.assertEqual(test_config.data_dir, self.data_dir / "ananke")
        self.assertEqual(test_config.backend, Backend.JSON)
        self.assertEqual(test_config.key_id, self.key_id)
        self.assertEqual(test_config.allow_multiple_keys, False)

    def test_build_with_defaults_nt_env(self) -> None:
        """Tests the 'build' method with NT defaults and an environment."""
        env = {
            "LOCALAPPDATA": str(self.data_dir),
        }

        test_config = ConfigBuilder(key_id=self.key_id, backend=Backend.JSON).with_defaults(OsFamily.NT, env).build()

        self.assertEqual(test_config.data_dir, self.data_dir / "ananke")
        self.assertEqual(test_config.backend, Backend.JSON)
        self.assertEqual(test_config.key_id, self.key_id)
        self.assertEqual(test_config.allow_multiple_keys, False)

    def test_build_with_env(self) -> None:
        """Tests the 'build' method with an environment."""
        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: "sqlite",
            Env.KEY_ID: str(self.key_id),
            Env.ALLOW_MULTIPLE_KEYS: "true",
        }

        test_config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()

        self.assertEqual(test_config.data_dir, self.data_dir)
        self.assertEqual(test_config.backend, Backend.SQLITE)
        self.assertEqual(test_config.key_id, self.key_id)
        self.assertEqual(test_config.allow_multiple_keys, True)

    def test_build_with_env_non_bool_allow_multiple_keys(self) -> None:
        """Tests the 'build' method with an environment and a non-boolean value for 'allow_multiple_keys'."""
        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: "sqlite",
            Env.KEY_ID: str(self.key_id),
            Env.ALLOW_MULTIPLE_KEYS: "invalid",
        }

        test_config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()

        self.assertEqual(test_config.allow_multiple_keys, False)

    def test_build_with_config_file(self) -> None:
        """Tests the 'build' method with a configuration file."""
        test_config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_config(config_reader).build()

        self.assertEqual(test_config.data_dir, Path(ConfigFile.DATA_DIR))
        self.assertEqual(test_config.backend, Backend.SQLITE)
        self.assertEqual(test_config.key_id, ConfigFile.KEY_ID)
        self.assertEqual(test_config.allow_multiple_keys, True)

    def test_build_with_config_file_with_env(self) -> None:
        """Tests the 'build' method with a configuration file and an environment."""
        key_id = KeyId("alice_env@example.com")

        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: "json",
            Env.KEY_ID: str(key_id),
            Env.ALLOW_MULTIPLE_KEYS: "false",
        }

        test_config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_config(config_reader).with_env(env).build()

        self.assertEqual(test_config.data_dir, self.data_dir)
        self.assertEqual(test_config.backend, Backend.JSON)
        self.assertEqual(test_config.key_id, key_id)
        self.assertEqual(test_config.allow_multiple_keys, False)

    def test_build_with_defaults_with_config_file_with_env(self) -> None:
        """Tests the 'build' method with defaults, a configuration file, and an environment."""
        partial_config_ini = textwrap.dedent(
            """\
            [data]
            backend=sqlite
            """
        )

        key_id = KeyId("alice_env@example.com")

        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.KEY_ID: str(key_id),
        }

        test_config = (
            ConfigBuilder()
            .with_defaults(OsFamily.POSIX, {})
            .with_config(lambda _: partial_config_ini)
            .with_env(env)
            .build()
        )

        self.assertEqual(test_config.data_dir, self.data_dir)
        self.assertEqual(test_config.backend, Backend.SQLITE)
        self.assertEqual(test_config.key_id, key_id)
        self.assertEqual(test_config.allow_multiple_keys, False)

        self.assertEqual(test_config.data_file, self.data_dir / "db" / "db.sqlite")

    def test_config_dir_posix(self) -> None:
        """Tests the 'config_dir' property with POSIX defaults."""
        test_config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_config(config_reader).build()
        self.assertEqual(test_config.config_dir, Path.home() / ".config" / "ananke")

    def test_config_dir_nt(self) -> None:
        """Tests the 'config_dir' property with NT defaults."""
        test_config = ConfigBuilder().with_defaults(OsFamily.NT, {}).with_config(config_reader).build()
        self.assertEqual(test_config.config_dir, Path.home() / "AppData" / "Roaming" / "ananke")

    def test_config_dir_with_xdg_config_home(self) -> None:
        """Tests the 'config_dir' property with an environment containing 'XDG_CONFIG_HOME'."""
        config_home = Path("/foo/bar")
        env = {
            "XDG_CONFIG_HOME": str(config_home),
        }
        test_config = ConfigBuilder().with_defaults(OsFamily.POSIX, env).with_config(config_reader).build()
        self.assertEqual(test_config.config_dir, config_home / "ananke")

    def test_config_dir_with_appdata(self) -> None:
        """Tests the 'config_dir' property with an environment containing 'APPDATA'."""
        config_home = Path("/foo/bar")
        env = {
            "APPDATA": str(config_home),
        }
        test_config = ConfigBuilder().with_defaults(OsFamily.NT, env).with_config(config_reader).build()
        self.assertEqual(test_config.config_dir, config_home / "ananke")


if __name__ == "__main__":
    unittest.main()
