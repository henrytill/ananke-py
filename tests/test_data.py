import datetime
import doctest
import unittest
from unittest import TestLoader, TestSuite

import tartarus.data as data


class TestParseTimestamp(unittest.TestCase):
    def test_parse_timestamp(self):
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54.640805116Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54, 640805),
        )

    def test_parse_timestamp_fewer_microseconds(self):
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54.640Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54, 640000),
        )

    def test_parse_timestamp_no_microseconds(self):
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54),
        )

    def test_parse_timestamp_no_seconds(self):
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58Z'),
            datetime.datetime(2023, 6, 7, 2, 58),
        )

    def test_parse_timestamp_invalid_format(self):
        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02:58:54:123Z')

        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02:58:54.123.456Z')

        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02Z')


def load_tests(loader: TestLoader, tests: TestSuite, ignore: object) -> TestSuite:
    tests.addTests(doctest.DocTestSuite(data))
    return tests


if __name__ == '__main__':
    unittest.main()
