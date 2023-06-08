import os
import shutil
import tempfile
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


class TestConfigBuilder(unittest.TestCase):
    def setUp(self):
        self.data_dir: Path = Path(tempfile.mkdtemp())
        os.makedirs(self.data_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.data_dir)

    def test_build(self):
        self.assertRaises(ValueError, ConfigBuilder().build)

    def test_build_with_defaults(self):
        self.assertRaises(ValueError, ConfigBuilder().with_defaults().build)

    def test_build_with_env(self):
        os.environ[Env.DATA_DIR] = str(Path('/foo/data'))
        os.environ[Env.BACKEND] = 'sqlite'
        os.environ[Env.KEY_ID] = 'test_key_id'
        os.environ[Env.ALLOW_MULTIPLE_KEYS] = 'true'

        config = ConfigBuilder().with_env().build()

        self.assertEqual(config.data_dir, Path('/foo/data'))
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, 'test_key_id')
        self.assertEqual(config.allow_multiple_keys, True)

    def test_build_with_config_file(self):
        config_file = self.data_dir / 'config.ini'
        with open(config_file, 'w') as f:
            f.write(str(ConfigFile()))

        config = ConfigBuilder().with_config_file(config_file).build()

        self.assertEqual(config.data_dir, Path(ConfigFile.DATA_DIR))
        self.assertEqual(config.backend, Backend.SQLITE)
        self.assertEqual(config.key_id, ConfigFile.KEY_ID)
        self.assertEqual(config.allow_multiple_keys, True)

    def test_build_with_config_file_and_env(self):
        config_file: Path = self.data_dir / 'config.ini'
        with open(config_file, 'w') as f:
            f.write(str(ConfigFile()))

        os.environ[Env.DATA_DIR] = str(Path('/foo/data'))
        os.environ[Env.BACKEND] = 'json'
        os.environ[Env.KEY_ID] = 'test_key_id_env'
        os.environ[Env.ALLOW_MULTIPLE_KEYS] = 'false'

        config = ConfigBuilder().with_config_file(config_file).with_env().build()

        self.assertEqual(config.data_dir, Path('/foo/data'))
        self.assertEqual(config.backend, Backend.JSON)
        self.assertEqual(config.key_id, 'test_key_id_env')
        self.assertEqual(config.allow_multiple_keys, False)


if __name__ == '__main__':
    unittest.main()
