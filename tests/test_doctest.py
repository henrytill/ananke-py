"""Module for running doctests via unittest discovery."""

import doctest
import unittest
from typing import Optional

from ananke.data import common


def load_tests(_loader: unittest.TestLoader, tests: unittest.TestSuite, _pattern: Optional[str]) -> unittest.TestSuite:
    """Load doctests into unittest's test suite."""
    tests.addTests(doctest.DocTestSuite(common))
    return tests


if __name__ == "__main__":
    unittest.main()
