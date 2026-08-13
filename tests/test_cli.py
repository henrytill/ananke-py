"""Tests for the command line interface."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from unittest.mock import patch

from ananke.cipher import KeyId, Plaintext
from ananke.cli import cmd_configure, format_results, main
from ananke.config import Backend, ConfigBuilder, Env, OsFamily
from ananke.data import Description, EntryId, Identity, SecureEntry, Timestamp


def make_record(description: str, identity: str, plaintext: str) -> SecureEntry:
    """Creates a record for formatting tests."""
    return SecureEntry(
        entry_id=EntryId.generate(),
        key_id=KeyId("371C136C"),
        timestamp=Timestamp.now(),
        description=Description(description),
        identity=Identity(identity),
        plaintext=Plaintext(plaintext),
        meta=None,
    )


class TestFormatResults(unittest.TestCase):
    """Tests for format_results."""

    def test_single_result_is_the_plaintext_alone(self) -> None:
        """Tests that a lone result is formatted as just its plaintext."""
        records: List[SecureEntry] = [make_record("https://www.foomail.com", "quux", "ASecretPassword")]

        self.assertEqual("ASecretPassword", format_results(list(records), verbose=False))

    def test_multiple_results_are_described(self) -> None:
        """Tests that ambiguous results carry enough context to tell them apart."""
        records: List[SecureEntry] = [
            make_record("https://www.foomail.com", "quux", "ASecretPassword"),
            make_record("https://www.foomail.com", "altquux", "ThisIsMyAltPassword"),
        ]

        expected = "\n".join(
            [
                "https://www.foomail.com quux ASecretPassword",
                "https://www.foomail.com altquux ThisIsMyAltPassword",
            ]
        )
        self.assertEqual(expected, format_results(list(records), verbose=False))

    def test_verbose_results_carry_the_entry_id(self) -> None:
        """Tests that verbose output includes the fields needed to address an entry."""
        record = make_record("https://www.foomail.com", "quux", "ASecretPassword")

        formatted = format_results([record], verbose=True)

        self.assertIn(str(record.entry_id), formatted)
        self.assertIn(record.timestamp.isoformat(), formatted)
        self.assertIn("371C136C", formatted)
        self.assertIn("ASecretPassword", formatted)


class TestConfigure(unittest.TestCase):
    """Tests for the configure command."""

    def setUp(self) -> None:
        # pylint: disable=consider-using-with
        self.dir = TemporaryDirectory(prefix="ananke-cli-test-")
        self.env = {
            Env.CONFIG_DIR: self.dir.name,
            Env.DATA_DIR: self.dir.name,
            Env.KEY_ID: "371C136C",
        }

    def tearDown(self) -> None:
        self.dir.cleanup()

    def _configure_with_input(self, backend_input: str) -> str:
        """Runs `configure`, answering the backend prompt with backend_input."""
        with patch("os.environ", self.env), patch("builtins.input", return_value=backend_input):
            with redirect_stdout(io.StringIO()):
                exit_code = cmd_configure(unittest.mock.Mock(list=False))

        self.assertEqual(0, exit_code)
        return (Path(self.dir.name) / "ananke.ini").read_text(encoding="utf-8")

    def test_backend_chosen_by_name(self) -> None:
        """Tests that the backend prompt accepts a backend name."""
        self.assertIn("backend=sqlite", self._configure_with_input("sqlite"))

    def test_backend_chosen_by_number(self) -> None:
        """Tests that the backend prompt accepts the numbers it offers.

        Every backend is offered by number, so entering one must select it rather
        than being rejected as invalid.
        """
        for backend in Backend:
            with self.subTest(backend=backend):
                self.setUp()
                try:
                    self.assertIn(f"backend={backend}", self._configure_with_input(str(backend.value)))
                finally:
                    self.tearDown()

    def test_empty_choice_takes_the_default(self) -> None:
        """Tests that an empty answer selects the default backend."""
        self.assertIn(f"backend={Backend.default()}", self._configure_with_input(""))

    def test_written_config_can_be_read_back(self) -> None:
        """Tests that configure writes a file that the config builder accepts."""
        self._configure_with_input("json")

        config = (
            ConfigBuilder()
            .with_defaults(OsFamily.POSIX, self.env)
            .with_config()
            .with_env({Env.KEY_ID: "371C136C"})
            .build()
        )

        self.assertEqual(Backend.JSON, config.backend)
        self.assertEqual(KeyId("371C136C"), config.key_id)


class TestMain(unittest.TestCase):
    """Tests for the top level error handling."""

    def test_failed_command_is_reported_without_a_traceback(self) -> None:
        """Tests that an expected failure is reported as a message on stderr."""
        stderr = io.StringIO()

        with patch("ananke.cli.cmd_lookup", side_effect=ValueError("No entries match zzz")):
            with redirect_stderr(stderr):
                exit_code = main(["lookup", "zzz"])

        self.assertEqual(1, exit_code)
        self.assertEqual("Error: No entries match zzz\n", stderr.getvalue())

    def test_unexpected_errors_still_propagate(self) -> None:
        """Tests that a defect is not disguised as a failed command."""
        with patch("ananke.cli.cmd_lookup", side_effect=AssertionError("boom")):
            with self.assertRaises(AssertionError):
                main(["lookup", "zzz"])


if __name__ == "__main__":
    unittest.main()
