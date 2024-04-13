import unittest
from dataclasses import dataclass

from ananke.application import Application, JsonApplication, SqliteApplication
from ananke.config import Config, ConfigBuilder, OsFamily
from ananke.data import Description, Plaintext


@dataclass(frozen=True)
class TestApplication:
    class Inner(unittest.TestCase):
        config: Config
        application: Application

        def test_add(self) -> None:
            """Tests the 'add' method"""
            self.application.add(description=Description("hello"), plaintext=Plaintext("world"))

        def test_lookup(self) -> None:
            """Tests the 'lookup' method"""
            results = self.application.lookup(description=Description("foo"))
            self.assertEqual(results, [])


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
