import unittest
from pathlib import Path
from textwrap import dedent

from tartarus import config
from tartarus.config import OS, Backend, ConfigBuilder, Env
from tartarus.data import KeyId


class TestOS(unittest.TestCase):
    def test_from_str(self):
        self.assertEqual(OS.from_str('posix'), OS.POSIX)
        self.assertEqual(OS.from_str('nt'), OS.NT)

    def test_from_str_with_invalid_os(self):
        self.assertRaises(ValueError, OS.from_str, 'invalid')

    def test_str(self):
        self.assertEqual(str(OS.POSIX), 'posix')
        self.assertEqual(str(OS.NT), 'nt')


class TestBackend(unittest.TestCase):
    def test_from_str(self):
        self.assertEqual(Backend.from_str('json'), Backend.JSON)
        self.assertEqual(Backend.from_str('sqlite'), Backend.SQLITE)

    def test_from_str_with_invalid_backend(self):
        self.assertRaises(ValueError, Backend.from_str, 'invalid')


class ConfigFile:
    BACKEND = 'sqlite'
    DATA_DIR = '/tmp/data'
    KEY_ID = 'alice.example.com'
    ALLOW_MULTIPLE_KEYS = 'true'

    def __str__(self):
        return dedent(
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
    def test_build(self):
        self.assertRaises(ValueError, ConfigBuilder().build)

    def test_build_with_defaults_posix(self):
        self.assertRaises(ValueError, ConfigBuilder().with_defaults(OS.POSIX).build)

    def test_build_with_defaults_nt(self):
        self.assertRaises(ValueError, ConfigBuilder().with_defaults(OS.NT).build)

    def test_build_without_data_dir(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                backend=Backend.SQLITE,
                key_id=KeyId('test_key_id'),
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_key_id(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=Path('/foo/data'),
                backend=Backend.SQLITE,
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_backend(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=Path('/foo/data'),
                key_id=KeyId('test_key_id'),
                allow_multiple_keys=True,
            ).build,
        )

    def test_build_without_allow_multiple_keys(self):
        self.assertRaises(
            ValueError,
            ConfigBuilder(
                data_dir=Path('/foo/data'),
                backend=Backend.SQLITE,
                key_id=KeyId('test_key_id'),
            ).build,
        )

    def test_build_with_defaults_posix_env(self):
        env = {
            'XDG_DATA_HOME': '/foo/data',
        }

        config = ConfigBuilder(key_id=KeyId('test_key_id')).with_defaults(OS.POSIX, env).build()

        self.assertEqual(config.data_dir, Path('/foo/data/tartarus'))
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, 'test_key_id')
        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_defaults_nt_env(self):
        env = {
            'LOCALAPPDATA': '/foo/data',
        }

        config = ConfigBuilder(key_id=KeyId('test_key_id')).with_defaults(OS.NT, env).build()

        self.assertEqual(config.data_dir, Path('/foo/data/tartarus'))
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, 'test_key_id')
        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_env(self):
        env = {
            Env.DATA_DIR: str(Path('/foo/data')),
            Env.BACKEND: 'sqlite',
            Env.KEY_ID: 'test_key_id',
            Env.ALLOW_MULTIPLE_KEYS: 'true',
        }

        config = ConfigBuilder().with_env(env).build()

        self.assertEqual(config.data_dir, Path('/foo/data'))
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, 'test_key_id')
        self.assertEqual(config.allow_multiple_keys, True)

    def test_build_with_env_non_bool_allow_multiple_keys(self):
        env = {
            Env.DATA_DIR: str(Path('/foo/data')),
            Env.BACKEND: 'sqlite',
            Env.KEY_ID: 'test_key_id',
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
        env = {
            Env.DATA_DIR: str(Path('/foo/data')),
            Env.BACKEND: 'json',
            Env.KEY_ID: 'test_key_id_env',
            Env.ALLOW_MULTIPLE_KEYS: 'false',
        }

        config = ConfigBuilder().with_config(str(ConfigFile())).with_env(env).build()

        self.assertEqual(config.data_dir, Path('/foo/data'))
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, 'test_key_id_env')
        self.assertEqual(config.allow_multiple_keys, False)

    def test_build_with_defaults_with_config_file_with_env(self):
        partial_config_ini = dedent(
            """\
            [data]
            backend=sqlite
            """
        )

        env = {
            Env.DATA_DIR: str(Path('/foo/data')),
            Env.KEY_ID: 'test_key_id_env',
        }

        config = ConfigBuilder().with_defaults(OS.POSIX).with_config(partial_config_ini).with_env(env).build()

        self.assertEqual(config.data_dir, Path('/foo/data'))
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, 'test_key_id_env')
        self.assertEqual(config.allow_multiple_keys, False)

        self.assertEqual(config.data_file, Path('/foo/data/db/data.json'))


class TestGetConfigFilePath(unittest.TestCase):
    def test_get_config_file_path_posix(self):
        path = config.get_config_file_path(OS.POSIX, {})
        self.assertEqual(path, Path.home() / '.config' / 'tartarus' / 'tartarus.ini')

    def test_get_config_file_path_nt(self):
        path = config.get_config_file_path(OS.NT, {})
        self.assertEqual(path, Path.home() / 'AppData' / 'Roaming' / 'tartarus' / 'tartarus.ini')

    def test_get_config_file_path_with_xdg_config_home(self):
        env = {
            'XDG_CONFIG_HOME': str(Path('/foo/bar')),
        }
        path = config.get_config_file_path(OS.POSIX, env)
        self.assertEqual(path, Path('/foo/bar/tartarus/tartarus.ini'))

    def test_get_config_file_path_with_appdata(self):
        env = {
            'APPDATA': str(Path('/foo/bar')),
        }
        path = config.get_config_file_path(OS.NT, env)
        self.assertEqual(path, Path('/foo/bar/tartarus/tartarus.ini'))


if __name__ == '__main__':
    unittest.main()
