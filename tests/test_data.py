"""Tests for the 'data' module."""
import datetime
import doctest
import unittest
from unittest import TestLoader, TestSuite

from tartarus import data


class TestParseTimestamp(unittest.TestCase):
    """Tests for the 'parse_timestamp' function."""

    def test_parse_timestamp(self):
        """Tests the 'parse_timestamp' function."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54.640805116Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54, 640805),
        )

    def test_parse_timestamp_fewer_microseconds(self):
        """Tests the 'parse_timestamp' function with fewer microseconds."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54.640Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54, 640000),
        )

    def test_parse_timestamp_no_microseconds(self):
        """Tests the 'parse_timestamp' function with no microseconds."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54),
        )

    def test_parse_timestamp_no_seconds(self):
        """Tests the 'parse_timestamp' function with no seconds."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58Z'),
            datetime.datetime(2023, 6, 7, 2, 58),
        )

    def test_parse_timestamp_invalid_format(self):
        """Tests the 'parse_timestamp' function with an invalid format."""
        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02:58:54:123Z')

        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02:58:54.123.456Z')

        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02Z')


# pylint: disable=unused-argument, missing-function-docstring
def load_tests(loader: TestLoader, tests: TestSuite, ignore: object) -> TestSuite:
    tests.addTests(doctest.DocTestSuite(data))
    return tests


if __name__ == '__main__':
    unittest.main()
