import os
import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, TypedDict, cast

from ananke.application import Application, JsonApplication, SqliteApplication, Target
from ananke.config import Config, ConfigBuilder, OsFamily
from ananke.data import Description, EntryId, Identity, Metadata, Plaintext

example_data: Path = Path("example") / "db" / "data.json"


class LookupArgs(TypedDict):
    """A type hint class for testing lookup."""

    description: Description
    maybe_identity: Optional[Identity]


class LookupTestCase(TypedDict):
    """A type hint class for testing lookup."""

    args: LookupArgs
    plaintexts: list[Plaintext]


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
        dir: TemporaryDirectory[str]
        config: Config
        application: Application

        def setUp(self) -> None:
            # pylint: disable=consider-using-with
            self.dir = TemporaryDirectory(prefix="ananke")

        def tearDown(self) -> None:
            self.dir.cleanup()

        def test_lookup(self) -> None:
            """Test the lookup method against the example data."""

            # see example/data.json for the test data
            test_cases: list[LookupTestCase] = [
                {
                    "args": {"description": Description("https://www.foomail.com"), "maybe_identity": Identity("quux")},
                    "plaintexts": [Plaintext("ASecretPassword")],
                },
                {
                    "args": {"description": Description("https://www.foomail.com"), "maybe_identity": None},
                    "plaintexts": [Plaintext("ASecretPassword")],
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
                    ],
                },
                {
                    "args": {"description": Description("www"), "maybe_identity": None},
                    "plaintexts": [
                        Plaintext("ASecretPassword"),
                        Plaintext("AnotherSecretPassword"),
                        Plaintext("YetAnotherSecretPassword"),
                    ],
                },
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    plaintexts = [plaintext for _, plaintext in self.application.lookup(**test_case["args"])]
                    self.assertEqual(test_case["plaintexts"], plaintexts)

        def test_add(self) -> None:
            """Test the add method against the example data."""

            test_cases: list[AddArgs] = [
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
                    results = self.application.lookup(test_case["description"], test_case["maybe_identity"])
                    self.assertEqual(1, len(results))
                    entry, plaintext = results[0]
                    self.assertEqual(self.config.key_id, entry.key_id)
                    self.assertEqual(test_case["description"], entry.description)
                    self.assertEqual(test_case["maybe_identity"], entry.identity)
                    self.assertEqual(test_case["plaintext"], plaintext)
                    self.assertEqual(test_case["maybe_meta"], entry.meta)

        def test_modify(self) -> None:
            """Test the modify method against the example data."""

            test_cases: list[ModifyArgs] = [
                {
                    "target": Description("https://www.foomail.com"),
                    "maybe_description": None,
                    "maybe_identity": Identity("quuxotic"),
                    "maybe_plaintext": None,
                    "maybe_meta": None,
                },
                {
                    "target": Description("https://www.foomail.com"),
                    "maybe_description": None,
                    "maybe_identity": None,
                    "maybe_plaintext": Plaintext("ANewSecretPasswordForFooMail"),
                    "maybe_meta": None,
                },
                {
                    "target": Description("https://www.foomail.com"),
                    "maybe_description": None,
                    "maybe_identity": None,
                    "maybe_plaintext": None,
                    "maybe_meta": Metadata('{ "foo": "bar" }'),
                },
                {
                    "target": Description("https://www.foomail.com"),
                    "maybe_description": Description("https://www.foonews.com"),
                    "maybe_identity": None,
                    "maybe_plaintext": None,
                    "maybe_meta": None,
                },
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

                    results = self.application.lookup(target)
                    self.assertEqual(1, len(results))
                    entry, plaintext = results[0]

                    self.application.modify(**test_case)

                    updated_results = self.application.lookup(
                        maybe_description if maybe_description is not None else target,
                        maybe_identity,
                    )
                    self.assertEqual(1, len(updated_results))
                    updated_entry, updated_plaintext = updated_results[0]

                    self.assertNotEqual(entry.entry_id, updated_entry.entry_id, "entry_id should change")
                    self.assertNotEqual(entry.timestamp, updated_entry.timestamp, "timestamp should change")

                    self.assertEqual(self.config.key_id, updated_entry.key_id, "key_id should not change")
                    self.assertEqual(
                        maybe_description if maybe_description is not None else entry.description,
                        updated_entry.description,
                        "description should change if provided",
                    )
                    self.assertEqual(
                        maybe_identity if maybe_identity is not None else entry.identity,
                        updated_entry.identity,
                        "identity should change if provided",
                    )
                    self.assertEqual(
                        maybe_plaintext if maybe_plaintext is not None else plaintext,
                        updated_plaintext,
                        "plaintext should change if provided",
                    )
                    self.assertEqual(
                        maybe_meta if maybe_meta is not None else entry.meta,
                        updated_entry.meta,
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

            test_cases: list[Description | EntryId] = [
                Description("https://www.foomail.com"),
                Description("https://www.bazbank.com"),
                Description("https://www.barphone.com"),
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    if isinstance(test_case, EntryId):
                        raise NotImplementedError

                    results = self.application.lookup(test_case)
                    self.assertEqual(1, len(results))
                    entry, _ = results[0]

                    self.application.remove(entry.entry_id)
                    results = self.application.lookup(test_case)
                    self.assertEqual(0, len(results))


# pylint: disable=abstract-method
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
        self.application.import_entries(example_data)
        os.environ["GNUPGHOME"] = "./example/gnupg"


# pylint: disable=abstract-method
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
        self.application.import_entries(example_data)
        os.environ["GNUPGHOME"] = "./example/gnupg"

    def tearDown(self) -> None:
        cast(SqliteApplication, self.application).close()
        return super().tearDown()
