import os
import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypedDict, cast

from ananke.application import (
    Application,
    JsonApplication,
    MultipleEntries,
    NoEntries,
    SqliteApplication,
    Target,
    TextApplication,
)
from ananke.cipher import Plaintext
from ananke.cli import EXPECTED_ERRORS
from ananke.config import Config, ConfigBuilder, OsFamily
from ananke.data import Description, EntryId, Identity, Metadata

EXPORT_ASC: Path = Path("example") / "export.asc"


class LookupArgs(TypedDict):
    """A type hint class for testing lookup."""

    description: Description
    maybe_identity: Identity | None


class LookupTestCase(TypedDict):
    """A type hint class for testing lookup."""

    args: LookupArgs
    plaintexts: list[Plaintext]


class AddArgs(TypedDict):
    """A type hint class for testing add."""

    description: Description
    plaintext: Plaintext
    maybe_identity: Identity | None
    maybe_meta: Metadata | None


class ModifyArgs(TypedDict):
    """A type hint class for testing modify."""

    target: Target
    maybe_description: Description | None
    maybe_identity: Identity | None
    maybe_plaintext: Plaintext | None
    maybe_meta: Metadata | None


@dataclass(frozen=True)
class TestApplication:
    class Inner(unittest.TestCase):
        backend: str

        def setUp(self) -> None:
            # pylint: disable=consider-using-with
            self.dir = TemporaryDirectory(prefix="ananke")
            os.environ["GNUPGHOME"] = str(Path.cwd() / "example" / "gnupg")
            env = {
                "ANANKE_CONFIG_DIR": f"{self.dir.name}",
                "ANANKE_DATA_DIR": f"{self.dir.name}",
                "ANANKE_KEY_ID": "371C136C",
                "ANANKE_BACKEND": self.backend,
            }
            self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
            self.open_application()
            self.application.import_entries(EXPORT_ASC)

        def tearDown(self) -> None:
            self.close_application()
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

        def open_application(self) -> None:
            """Opens an application against the current configuration.

            Overridden by each backend's test case, so that shared tests can reopen
            a store without knowing which backend they are exercising.
            """
            raise NotImplementedError

        def close_application(self) -> None:
            """Releases any resources the application holds."""

        def test_lookup(self) -> None:
            """Test the lookup method against the example data."""

            # see example/data.json for the test data
            test_cases: list[LookupTestCase] = [
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

            test_cases: list[ModifyArgs] = [
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

            with self.assertRaises(NoEntries) as exc:
                self.application.modify(target, None, None, None, None)

            self.assertEqual(f"No entries match {target}", str(exc.exception))

        def test_modify_fails_if_multiple_entries_match(self) -> None:
            """Test that modify fails if multiple entries match."""

            target = Description("https://www.foomail.com")

            with self.assertRaises(MultipleEntries) as exc:
                self.application.modify(target, None, None, None, None)

            self.assertEqual(f"Multiple entries match {target}", str(exc.exception))

        def test_modify_fails_on_partial_description(self) -> None:
            """Test that a target matches a description exactly, not as a substring."""

            target = Description("foomail")

            with self.assertRaises(NoEntries) as exc:
                self.application.modify(target, None, None, None, None)

            self.assertEqual(f"No entries match {target}", str(exc.exception))

        def test_remove(self) -> None:
            """Test the remove method against the example data."""

            test_cases: list[Description] = [
                Description("https://www.bazbank.com"),
                Description("https://www.barphone.com"),
            ]

            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    records = self.application.lookup(test_case)
                    self.assertEqual(1, len(records))
                    record = records[0]

                    self.application.remove(record.entry_id)
                    records = self.application.lookup(test_case)
                    self.assertEqual(0, len(records))

        def test_remove_by_description(self) -> None:
            """Test that remove accepts a description as a target."""

            target = Description("https://www.bazbank.com")

            self.assertEqual(1, len(self.application.lookup(target)))
            self.application.remove(target)
            self.assertEqual(0, len(self.application.lookup(target)))

        def test_remove_fails_if_no_entries_match(self) -> None:
            """Test that remove fails, rather than silently doing nothing, if no entries match."""

            test_cases: list[Description] = [
                Description("zzz"),
                # a partial description matches no entry: targets are matched exactly
                Description("bazbank"),
            ]

            for target in test_cases:
                with self.subTest(target=target):
                    with self.assertRaises(NoEntries) as exc:
                        self.application.remove(target)

                    self.assertEqual(f"No entries match {target}", str(exc.exception))
                    self.assertEqual(4, len(self.application.lookup(Description("www"))))

        def test_remove_fails_if_multiple_entries_match(self) -> None:
            """Test that remove fails, rather than removing every match, if multiple entries match."""

            target = Description("https://www.foomail.com")

            self.assertEqual(2, len(self.application.lookup(target)))

            with self.assertRaises(MultipleEntries) as exc:
                self.application.remove(target)

            self.assertEqual(f"Multiple entries match {target}", str(exc.exception))
            self.assertEqual(2, len(self.application.lookup(target)))

        def test_lookup_with_an_empty_description(self) -> None:
            """Test that an empty description constrains nothing, rather than failing.

            The SQLite backend used to build a query with an empty WHERE clause here
            and fail with an OperationalError, while the others returned everything.
            """

            self.assertEqual(4, len(self.application.lookup(Description(""))))

        def test_lookup_with_an_empty_identity(self) -> None:
            """Test that an empty identity constrains nothing, rather than failing."""

            self.assertEqual(4, len(self.application.lookup(Description("www"), Identity(""))))

        def test_clear(self) -> None:
            """Test that clear empties the store, and that the store stays usable."""

            self.assertEqual(4, len(self.application.lookup(Description("www"))))

            self.application.clear()

            self.assertEqual(0, len(self.application.lookup(Description("www"))))

            # An emptied store still accepts entries, rather than having had the
            # files it needs deleted out from under it.
            self.application.add(Description("https://www.bazlib.org/"), Plaintext("bazlibpass"))
            self.assertEqual(1, len(self.application.lookup(Description("bazlib"))))

        def test_clear_is_idempotent(self) -> None:
            """Test that clearing an already empty store is not an error."""

            self.application.clear()
            self.application.clear()

            self.assertEqual(0, len(self.application.lookup(Description("www"))))

        def test_import_of_an_already_imported_file(self) -> None:
            """Characterizes what a repeated import does to each backend.

            The backends disagree, and so does the reference implementation, which
            this follows: SQLite replaces by entry id, while JSON and Text append,
            producing two entries that share an id and that no target can then
            address.  See henrytill/ananke#143.  This test pins the current
            behaviour so that a change to it is a deliberate one.
            """

            self.application.import_entries(EXPORT_ASC)

            found = len(self.application.lookup(Description("https://www.bazbank.com")))
            expected = 1 if isinstance(self.application, SqliteApplication) else 2

            self.assertEqual(expected, found)

        def test_import_of_a_corrupt_file(self) -> None:
            """Test that a file which is not a valid store is rejected, not partly applied."""

            before = len(self.application.lookup(Description("www")))

            corrupt = Path(self.dir.name) / "corrupt.asc"
            corrupt.write_text("this is not an encrypted export", encoding="utf-8")

            with self.assertRaises(ValueError):
                self.application.import_entries(corrupt)

            self.assertEqual(before, len(self.application.lookup(Description("www"))))

        def test_opening_a_corrupt_store(self) -> None:
            """Test that a damaged store fails in a way the CLI can report.

            The backends raise different types here -- a JSON decode error, a gpg
            failure, a sqlite3 error -- so what matters is that each is one the
            command line reports as a message rather than a traceback.
            """

            self.close_application()
            self.config.data_file.write_text("this is not a store", encoding="utf-8")

            with self.assertRaises(EXPECTED_ERRORS):
                self.open_application()

        def test_import_of_a_missing_file(self) -> None:
            """Test that importing a file that is not there says so."""

            with self.assertRaises(FileNotFoundError):
                self.application.import_entries(Path(self.dir.name) / "nonexistent.asc")

        def test_export_import(self) -> None:
            """Test that exported data can be re-imported."""

            entries = self.application.lookup(Description("www"))
            self.assertEqual(4, len(entries))

            file = Path(self.dir.name) / "export.asc"
            self.application.export_entries(file)
            self.assertTrue(file.exists())

            self.application.clear()
            self.assertEqual(0, len(self.application.lookup(Description("www"))))

            self.application.import_entries(file)
            imported_entries = self.application.lookup(Description("www"))
            self.assertEqual(4, len(imported_entries))
            self.assertEqual(entries, imported_entries)


class TestJsonApplication(TestApplication.Inner):
    backend = "json"

    def open_application(self) -> None:
        self.application = JsonApplication(self.config)


class TestSqliteApplication(TestApplication.Inner):
    backend = "sqlite"

    def open_application(self) -> None:
        self.application = SqliteApplication(self.config)

    def close_application(self) -> None:
        cast(SqliteApplication, self.application).close()


class TestTextApplication(TestApplication.Inner):
    backend = "text"

    def open_application(self) -> None:
        self.application = TextApplication(self.config)
