"""Common datatypes and related functions."""

import base64
import binascii
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Any, NewType, Optional, Self
from uuid import UUID

KeyId = NewType("KeyId", str)
"""A Cryptographic Key Id."""

Description = NewType("Description", str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType("Identity", str)
"""An identifying value, such as the username in a username/password pair."""

Metadata = NewType("Metadata", str)
"""Contains additional non-specific information for an 'Entry'."""


class Timestamp:
    """A UTC timestamp.

    Attributes:
        value: The datetime object.
    """

    value: datetime

    def __init__(self, value: datetime) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timestamp):
            return False
        return self.value.__eq__(other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Timestamp):
            raise TypeError(f"'<' not supported between instances of 'Timestamp' and '{type(other).__name__}'")
        return self.value.__lt__(other.value)

    @classmethod
    def now(cls) -> Self:
        """Creates a Timestamp object with the current time."""
        return cls(datetime.now(timezone.utc))

    @classmethod
    def fromisoformat(cls, timestamp: str) -> Self:
        """Creates a Timestamp object from an ISO 8601 string.

        Args:
            timestamp: The ISO 8601 string.

        Returns:
            The Timestamp object.

        Raises:
            ValueError: If the timestamp is in an invalid format.
        """
        return cls(datetime.fromisoformat(timestamp))

    def isoformat(self) -> str:
        """Returns the timestamp as an ISO 8601 string."""
        return self.value.isoformat().replace("+00:00", "Z")


class Plaintext:
    """A plaintext value.

    Attributes:
        value: The plaintext value.
    """

    value: str

    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Plaintext):
            return False
        return self.value.__eq__(other.value)

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return f"Plaintext({self.value!r})"

    def __len__(self) -> int:
        return self.value.__len__()

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        """Encodes the plaintext value using the specified encoding.

        Args:
            encoding: The encoding to use.
            errors: The error handling scheme to use for encoding errors.

        Returns:
            The encoded value.
        """
        return self.value.encode(encoding, errors)

    @classmethod
    def random(
        cls,
        length: int,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_punctuation: bool = False,
    ) -> Self:
        """Generates a random Plaintext of a given length.

        Args:
            length: The length of the generated string.
            use_lowercase: Whether to use lowercase letters.
            use_uppercase: Whether to use uppercase letters.
            use_digits: Whether to use digits.
            use_punctuation: Whether to use punctuation.

        Returns:
            A random Plaintext of the specified length.
        """
        chars = string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_digits:
            chars += string.digits
        if use_punctuation:
            chars += string.punctuation

        ret = "".join(secrets.choice(chars) for _ in range(length))

        return cls(ret)


class Ciphertext(bytes):
    """An encrypted value of an 'Entry'."""

    def __new__(cls, value: bytes) -> Self:
        return super().__new__(cls, value)

    @classmethod
    def from_base64(cls, value: str) -> Self:
        """Creates a Ciphertext object from a base64 encoded string.

        Args:
            value: The base64 encoded string.

        Returns:
            The Ciphertext object.

        Raises:
            ValueError: If the value is not a valid base64 encoded string.
        """
        try:
            return cls(base64.b64decode(value.encode("ascii")))
        except binascii.Error as exc:
            raise ValueError("Invalid base64 string") from exc

    def to_base64(self) -> str:
        """Encodes the Ciphertext object as a base64 string.

        Returns:
            The base64 encoded string.
        """
        return base64.b64encode(self).decode("ascii")


class EntryId:
    """Uniquely identifies an 'Entry'.

    Attributes:
        value: The entry id.
    """

    value: UUID

    def __init__(self, value: UUID | str) -> None:
        if isinstance(value, UUID):
            self.value = value
        else:
            self.value = UUID(value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntryId):
            return False
        return self.value.__eq__(other.value)

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return f"EntryId({self.value!r})"

    def __hash__(self) -> int:
        return self.value.__hash__()

    @classmethod
    def generate(cls) -> Self:
        """Generates an EntryId.

        Returns:
            The generated EntryId.
        """
        return cls(uuid.uuid4())


def remap_keys(mapping: dict[str, str], data: dict[str, Any]) -> dict[str, Any]:
    """Maps the keys of a dictionary to a new set of keys.

    If a key is not present in the mapping, it is left unchanged.

    Args:
        mapping: A dictionary that maps the old keys to the new keys.
        data: The dictionary to transform.

    Returns:
        A new dictionary where the keys have been replaced according to the mapping.

    Examples:
    >>> remap_keys({"a": "b"}, {"a": 1})
    {'b': 1}
    >>> remap_keys({"a": "b"}, {"a": 1, "c": 2})
    {'b': 1, 'c': 2}
    >>> remap_keys({"a": "b"}, {"c": 1})
    {'c': 1}
    """
    return {mapping.get(key, key): value for key, value in data.items()}


def get_required(d: dict[Any, Any], key: Any, value_type: type) -> Any:
    """Gets a required value from a dictionary.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.
        value_type: The type of the value.

    Returns:
        The value.

    Examples:
    >>> get_required({"a": 1}, "a", int)
    1
    >>> get_required({"a": 1}, "a", str)
    Traceback (most recent call last):
    ...
    TypeError: Invalid a: expected a value of type <class 'str'>
    >>> get_required({"a": 1}, "b", int)
    Traceback (most recent call last):
    ...
    KeyError: 'Invalid entry: missing required key: b'
    """
    value = d.get(key)
    if value is None:
        raise KeyError(f"Invalid entry: missing required key: {key}")
    if not isinstance(value, value_type):
        raise TypeError(f"Invalid {key}: expected a value of type {value_type}")
    return value


def get_optional(d: dict[Any, Any], key: Any, value_type: type) -> Optional[Any]:
    """Gets an optional value from a dictionary.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.
        value_type: The type of the value.

    Returns:
        The value, or None if the key is not present.

    Examples:
    >>> get_optional({"a": 1}, "a", int)
    1
    >>> get_optional({"a": 1}, "a", str)
    Traceback (most recent call last):
    ...
    TypeError: Invalid a: expected a value of type <class 'str'>
    >>> get_optional({"a": 1}, "b", int) is None
    True
    """
    value = d.get(key)
    if value is None:
        return None
    if not isinstance(value, value_type):
        raise TypeError(f"Invalid {key}: expected a value of type {value_type}")
    return value
