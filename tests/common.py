"""Common code for tests."""
from typing import TypedDict


class RandomArgs(TypedDict):
    """Type hint class for the 'test_random' method."""

    length: int
    use_uppercase: bool
    use_digits: bool
    use_punctuation: bool
