import unittest
from pathlib import Path
from textwrap import dedent

from tartarus.config import Backend, ConfigBuilder, Env


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


class TestBackend(unittest.TestCase):
    def test_from_str(self):
        self.assertEqual(Backend.from_str('json'), Backend.JSON)
        self.assertEqual(Backend.from_str('sqlite'), Backend.SQLITE)

    def test_from_str_with_invalid_backend(self):
        self.assertRaises(ValueError, Backend.from_str, 'invalid')


class TestConfigBuilder(unittest.TestCase):
    def test_build(self):
        self.assertRaises(ValueError, ConfigBuilder().build)

    def test_build_with_defaults(self):
        self.assertRaises(ValueError, ConfigBuilder().with_defaults().build)

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

    def test_build_with_non_bool_allow_multiple_keys(self):
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

    def test_build_with_config_file_and_env(self):
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

        config = ConfigBuilder().with_defaults().with_config(partial_config_ini).with_env(env).build()

        self.assertEqual(config.data_dir, Path('/foo/data'))
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, 'test_key_id_env')
        self.assertEqual(config.allow_multiple_keys, False)

        self.assertEqual(config.data_file, Path('/foo/data/db/data.json'))


if __name__ == '__main__':
    unittest.main()
