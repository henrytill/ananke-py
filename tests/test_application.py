import os
import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, TypedDict, cast

from ananke.application import Application, JsonApplication, SqliteApplication, Target
from ananke.cipher import Plaintext
from ananke.config import Config, ConfigBuilder, OsFamily
from ananke.data import Description, EntryId, Identity, Metadata

EXPORT_ASC: Path = Path("example") / "export.asc"


class LookupArgs(TypedDict):
    """A type hint class for testing lookup."""

    description: Description
    maybe_identity: Optional[Identity]


class LookupTestCase(TypedDict):
    """A type hint class for testing lookup."""

    args: LookupArgs
    plaintexts: List[Plaintext]


class AddArgs(TypedDict):
    """A type hint class for testing add."""

    description: Description
    plaintext: Plaintext
    maybe_identity: Optional[Identity]
    maybe_meta: Optional[Metadata]


class ModifyArgs(TypedDict):
    """A type hint class for testing modify."""

    target: Target
    maybe_description: Optional[Description]
    maybe_identity: Optional[Identity]
    maybe_plaintext: Optional[Plaintext]
    maybe_meta: Optional[Metadata]


@dataclass(frozen=True)
class TestApplication:
    class Inner(unittest.TestCase):
        def setUp(self) -> None:
            # pylint: disable=consider-using-with
            self.dir = TemporaryDirectory(prefix="ananke")
            os.environ["GNUPGHOME"] = str(Path.cwd() / "example" / "gnupg")

        def tearDown(self) -> None:
            self.dir.cleanup()

        @property
        def config(self) -> Config:
            """The configuration to test."""
            return self._config

        @config.setter
        def config(self, config: Config) -> None:
            self._config = config

        @property
        def application(self) -> Application:
            """The application to test."""
            return self._application

        @application.setter
        def application(self, application: Application) -> None:
            self._application = application

        def test_lookup(self) -> None:
            """Test the lookup method against the example data."""

            # see example/data.json for the test data
            test_cases: List[LookupTestCase] = [
                {
                    "args": {"description": Description("https://www.foomail.com"), "maybe_identity": Identity("quux")},
                    "plaintexts": [Plaintext("ASecretPassword"), Plaintext("ThisIsMyAltPassword")],
                },
                {
                    "args": {"description": Description("https://www.foomail.com"), "maybe_identity": None},
                    "plaintexts": [Plaintext("ASecretPassword"), Plaintext("ThisIsMyAltPassword")],
                },
                {
                    "args": {"description": Description("https://www.bazbank.com"), "maybe_identity": Identity("quux")},
                    "plaintexts": [Plaintext("AnotherSecretPassword")],
                },
                {
                    "args": {"description": Description("https://www.bazbank.com"), "maybe_identity": None},
                    "plaintexts": [Plaintext("AnotherSecretPassword")],
                },
                {
                    "args": {
                        "description": Description("https://www.barphone.com"),
                        "maybe_identity": Identity("quux"),
                    },
                    "plaintexts": [Plaintext("YetAnotherSecretPassword")],
                },
                {
                    "args": {"description": Description("https://www.barphone.com"), "maybe_identity": None},
                    "plaintexts": [Plaintext("YetAnotherSecretPassword")],
                },
                {
                    "args": {"description": Description("www"), "maybe_identity": Identity("quux")},
                    "plaintexts": [
                        Plaintext("ASecretPassword"),
                        Plaintext("AnotherSecretPassword"),
                        Plaintext("YetAnotherSecretPassword"),
                        Plaintext("ThisIsMyAltPassword"),
                    ],
                },
                {
                    "args": {"description": Description("www"), "maybe_identity": None},
                    "plaintexts": [
                        Plaintext("ASecretPassword"),
                        Plaintext("AnotherSecretPassword"),
                        Plaintext("YetAnotherSecretPassword"),
                        Plaintext("ThisIsMyAltPassword"),
                    ],
                },
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    plaintexts = [record.plaintext for record in self.application.lookup(**test_case["args"])]
                    self.assertEqual(test_case["plaintexts"], plaintexts)

        def test_add(self) -> None:
            """Test the add method against the example data."""

            test_cases: List[AddArgs] = [
                {
                    "description": Description("https://www.foonews.com"),
                    "plaintext": Plaintext("FooNewsSecretPassword"),
                    "maybe_identity": Identity("quux@foomail.com"),
                    "maybe_meta": None,
                },
                {
                    "description": Description("https://www.bazblog.com"),
                    "plaintext": Plaintext("BazBlogSecretPassword"),
                    "maybe_identity": Identity("quux@foomail.com"),
                    "maybe_meta": Metadata('{ "foo": "bar" }'),
                },
                {
                    "description": Description("https://www.barsounds.com"),
                    "plaintext": Plaintext("BarSoundsSecretPassword"),
                    "maybe_identity": None,
                    "maybe_meta": None,
                },
                {
                    "description": Description("https://www.fooblog.com"),
                    "plaintext": Plaintext("FooBlogSecretPassword"),
                    "maybe_identity": None,
                    "maybe_meta": Metadata('{ "foo": "bar" }'),
                },
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    self.application.add(**test_case)
                    records = self.application.lookup(test_case["description"], test_case["maybe_identity"])
                    self.assertEqual(1, len(records))
                    record = records[0]
                    self.assertEqual(self.config.key_id, record.key_id)
                    self.assertEqual(test_case["description"], record.description)
                    self.assertEqual(test_case["maybe_identity"], record.identity)
                    self.assertEqual(test_case["plaintext"], record.plaintext)
                    self.assertEqual(test_case["maybe_meta"], record.meta)

        def test_modify(self) -> None:
            """Test the modify method against the example data."""

            test_cases: List[ModifyArgs] = [
                {
                    "target": Description("https://www.bazbank.com"),
                    "maybe_description": None,
                    "maybe_identity": Identity("quuxotic"),
                    "maybe_plaintext": None,
                    "maybe_meta": None,
                },
                {
                    "target": Description("https://www.bazbank.com"),
                    "maybe_description": None,
                    "maybe_identity": None,
                    "maybe_plaintext": Plaintext("ANewSecretPasswordForBazBank"),
                    "maybe_meta": None,
                },
                {
                    "target": Description("https://www.bazbank.com"),
                    "maybe_description": None,
                    "maybe_identity": None,
                    "maybe_plaintext": None,
                    "maybe_meta": Metadata('{ "foo": "bar" }'),
                },
                {
                    "target": Description("https://www.bazbank.com"),
                    "maybe_description": Description("https://www.bazblog.com"),
                    "maybe_identity": None,
                    "maybe_plaintext": None,
                    "maybe_meta": None,
                },
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    target = test_case["target"]
                    maybe_description = test_case["maybe_description"]
                    maybe_identity = test_case["maybe_identity"]
                    maybe_plaintext = test_case["maybe_plaintext"]
                    maybe_meta = test_case["maybe_meta"]

                    if isinstance(target, EntryId):
                        raise NotImplementedError

                    records = self.application.lookup(target)
                    self.assertEqual(1, len(records))
                    record = records[0]

                    self.application.modify(**test_case)

                    updated_records = self.application.lookup(
                        maybe_description if maybe_description is not None else target,
                        maybe_identity,
                    )
                    self.assertEqual(1, len(updated_records))
                    updated_record = updated_records[0]

                    self.assertEqual(record.entry_id, updated_record.entry_id, "entry_id should not change")
                    self.assertNotEqual(record.timestamp, updated_record.timestamp, "timestamp should change")

                    self.assertEqual(self.config.key_id, updated_record.key_id, "key_id should not change")
                    self.assertEqual(
                        maybe_description if maybe_description is not None else record.description,
                        updated_record.description,
                        "description should change if provided",
                    )
                    self.assertEqual(
                        maybe_identity if maybe_identity is not None else record.identity,
                        updated_record.identity,
                        "identity should change if provided",
                    )
                    self.assertEqual(
                        maybe_plaintext if maybe_plaintext is not None else record.plaintext,
                        updated_record.plaintext,
                        "plaintext should change if provided",
                    )
                    self.assertEqual(
                        maybe_meta if maybe_meta is not None else record.meta,
                        updated_record.meta,
                        "meta should change if provided",
                    )

        def test_modify_fails_if_no_entries_match(self) -> None:
            """Test that modify fails if no entries match."""

            target = Description("zzz")

            with self.assertRaises(ValueError) as exc:
                self.application.modify(target, None, None, None, None)

            self.assertEqual(f"No entries match {target}", str(exc.exception))

        def test_modify_fails_if_multiple_entries_match(self) -> None:
            """Test that modify fails if multiple entries match."""

            target = Description("www")

            with self.assertRaises(ValueError) as exc:
                self.application.modify(target, None, None, None, None)

            self.assertEqual(f"Multiple entries match {target}", str(exc.exception))

        def test_remove(self) -> None:
            """Test the remove method against the example data."""

            test_cases: List[Description | EntryId] = [
                Description("https://www.bazbank.com"),
                Description("https://www.barphone.com"),
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    if isinstance(test_case, EntryId):
                        raise NotImplementedError

                    records = self.application.lookup(test_case)
                    self.assertEqual(1, len(records))
                    record = records[0]

                    self.application.remove(record.entry_id)
                    records = self.application.lookup(test_case)
                    self.assertEqual(0, len(records))


class TestJsonApplication(TestApplication.Inner):
    def setUp(self) -> None:
        super().setUp()
        env = {
            "ANANKE_CONFIG_DIR": f"{self.dir.name}",
            "ANANKE_DATA_DIR": f"{self.dir.name}",
            "ANANKE_KEY_ID": "371C136C",
            "ANANKE_BACKEND": "json",
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
        self.application = JsonApplication(self.config)
        self.application.import_entries(EXPORT_ASC)


class TestSqliteApplication(TestApplication.Inner):
    def setUp(self) -> None:
        super().setUp()
        env = {
            "ANANKE_CONFIG_DIR": f"{self.dir.name}",
            "ANANKE_DATA_DIR": f"{self.dir.name}",
            "ANANKE_KEY_ID": "371C136C",
            "ANANKE_BACKEND": "sqlite",
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
        self.application = SqliteApplication(self.config)
        self.application.import_entries(EXPORT_ASC)

    def tearDown(self) -> None:
        cast(SqliteApplication, self.application).close()
        return super().tearDown()
