import unittest
from dataclasses import dataclass

from ananke.application import Application, JsonApplication, SqliteApplication
from ananke.config import Config, ConfigBuilder, OsFamily


@dataclass(frozen=True)
class TestApplication:
    class Inner(unittest.TestCase):
        config: Config
        application: Application

        @unittest.skip("unimplemented")
        def test_add(self) -> None:
            """Tests the 'add' method"""
            raise NotImplementedError

        @unittest.skip("unimplemented")
        def test_lookup(self) -> None:
            """Tests the 'lookup' method"""
            raise NotImplementedError


class TestJsonApplication(TestApplication.Inner):
    def setUp(self) -> None:
        env = {
            "ANANKE_DATA_DIR": "./example",
            "ANANKE_KEY_ID": "371C136C",
            "ANANKE_BACKEND": "json",
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
        self.application = JsonApplication(self.config)


class TestSqliteApplication(TestApplication.Inner):
    def setUp(self) -> None:
        env = {
            "ANANKE_DATA_DIR": "./example",
            "ANANKE_KEY_ID": "371C136C",
            "ANANKE_BACKEND": "sqlite",
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
        self.application = SqliteApplication(self.config)
