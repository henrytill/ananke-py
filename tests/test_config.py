import textwrap
import unittest
from pathlib import Path

from tartarus import config
from tartarus.config import Backend, ConfigBuilder, Env, OsFamily
from tartarus.data import KeyId


class TestOsFamily(unittest.TestCase):
    def test_from_str(self):
        self.assertEqual(OsFamily.from_str('posix'), OsFamily.POSIX)
        self.assertEqual(OsFamily.from_str('nt'), OsFamily.NT)

    def test_from_str_with_invalid_os(self):
        self.assertRaises(ValueError, OsFamily.from_str, 'invalid')

    def test_str(self):
        self.assertEqual(str(OsFamily.POSIX), 'posix')
        self.assertEqual(str(OsFamily.NT), 'nt')


class TestBackend(unittest.TestCase):
    def test_from_str(self):
        self.assertEqual(Backend.from_str('json'), Backend.JSON)
        self.assertEqual(Backend.from_str('sqlite'), Backend.SQLITE)

    def test_from_str_with_invalid_backend(self):
        self.assertRaises(ValueError, Backend.from_str, 'invalid')


class ConfigFile:
    BACKEND = 'sqlite'
    DATA_DIR = '/tmp/data'
    KEY_ID = 'alice_file@example.com'
    ALLOW_MULTIPLE_KEYS = 'true'

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


class TestConfigBuilder(unittest.TestCase):
    data_dir = Path('/foo/bar')
    key_id = KeyId('alice@example.com')

    def test_build(self):
        self.assertRaises(ValueError, ConfigBuilder().build)

    def test_build_with_defaults_posix(self):
        self.assertRaises(ValueError, ConfigBuilder().with_defaults(OsFamily.POSIX).build)

    def test_build_with_defaults_nt(self):
        self.assertRaises(ValueError, ConfigBuilder().with_defaults(OsFamily.NT).build)

    def test_build_without_data_dir(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                backend=Backend.SQLITE,
                key_id=self.key_id,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_key_id(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=self.data_dir,
                backend=Backend.SQLITE,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_backend(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=self.data_dir,
                key_id=self.key_id,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_allow_multiple_keys(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=self.data_dir,
                backend=Backend.SQLITE,
                key_id=self.key_id,
            ).build,
        )

    def test_build_with_defaults_posix_env(self):
        env = {
            'XDG_DATA_HOME': str(self.data_dir),
        }

        config = ConfigBuilder(key_id=self.key_id).with_defaults(OsFamily.POSIX, env).build()

        self.assertEqual(config.data_dir, self.data_dir / 'tartarus')
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, self.key_id)
        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_defaults_nt_env(self):
        env = {
            'LOCALAPPDATA': str(self.data_dir),
        }

        config = ConfigBuilder(key_id=self.key_id).with_defaults(OsFamily.NT, env).build()

        self.assertEqual(config.data_dir, self.data_dir / 'tartarus')
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, self.key_id)
        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_env(self):
        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: 'sqlite',
            Env.KEY_ID: str(self.key_id),
            Env.ALLOW_MULTIPLE_KEYS: 'true',
        }

        config = ConfigBuilder().with_env(env).build()

        self.assertEqual(config.data_dir, self.data_dir)
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, self.key_id)
        self.assertEqual(config.allow_multiple_keys, True)

    def test_build_with_env_non_bool_allow_multiple_keys(self):
        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: 'sqlite',
            Env.KEY_ID: str(self.key_id),
            Env.ALLOW_MULTIPLE_KEYS: 'invalid',
        }

        config = ConfigBuilder().with_env(env).build()

        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_config_file(self):
        config = ConfigBuilder().with_config(str(ConfigFile())).build()

        self.assertEqual(config.data_dir, Path(ConfigFile.DATA_DIR))
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, ConfigFile.KEY_ID)
        self.assertEqual(config.allow_multiple_keys, True)

    def test_build_with_config_file_with_env(self):
        key_id = KeyId('alice_env@example.com')

        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.BACKEND: 'json',
            Env.KEY_ID: str(key_id),
            Env.ALLOW_MULTIPLE_KEYS: 'false',
        }

        config = ConfigBuilder().with_config(str(ConfigFile())).with_env(env).build()

        self.assertEqual(config.data_dir, self.data_dir)
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, key_id)
        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_defaults_with_config_file_with_env(self):
        partial_config_ini = textwrap.dedent(
            """\
            [data]
            backend=sqlite
            """
        )

        key_id = KeyId('alice_env@example.com')

        env = {
            Env.DATA_DIR: str(self.data_dir),
            Env.KEY_ID: str(key_id),
        }

        config = ConfigBuilder().with_defaults(OsFamily.POSIX).with_config(partial_config_ini).with_env(env).build()

        self.assertEqual(config.data_dir, self.data_dir)
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, key_id)
        self.assertEqual(config.allow_multiple_keys, False)

        self.assertEqual(config.data_file, self.data_dir / 'db' / 'data.json')


class TestGetConfigFilePath(unittest.TestCase):
    config_home = Path('/foo/bar')

    def test_get_config_file_path_posix(self):
        path = config.get_config_file(OsFamily.POSIX, {})
        self.assertEqual(path, Path.home() / '.config' / 'tartarus' / 'tartarus.ini')

    def test_get_config_file_path_nt(self):
        path = config.get_config_file(OsFamily.NT, {})
        self.assertEqual(path, Path.home() / 'AppData' / 'Roaming' / 'tartarus' / 'tartarus.ini')

    def test_get_config_file_path_with_xdg_config_home(self):
        env = {
            'XDG_CONFIG_HOME': str(self.config_home),
        }
        path = config.get_config_file(OsFamily.POSIX, env)
        self.assertEqual(path, self.config_home / 'tartarus' / 'tartarus.ini')

    def test_get_config_file_path_with_appdata(self):
        env = {
            'APPDATA': str(self.config_home),
        }
        path = config.get_config_file(OsFamily.NT, env)
        self.assertEqual(path, self.config_home / 'tartarus' / 'tartarus.ini')


if __name__ == '__main__':
    unittest.main()
