"""Core data structures and related functions."""
import base64
import binascii
import re
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, NewType, Optional, TypedDict

KeyId = NewType('KeyId', str)
"""Represents a GPG Key Id."""

EntryId = NewType('EntryId', str)
"""Uniquely identifies an 'Entry'."""

Description = NewType('Description', str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType('Identity', str)
"""Represents an identifying value, such as the username in a username/password pair."""

Metadata = NewType('Metadata', str)
"""Contains additional non-specific information for an 'Entry'."""


class Timestamp:
    """Represents a UTC timestamp."""

    def __init__(self, timestamp: datetime):
        self.timestamp = timestamp

    @classmethod
    def now(cls) -> 'Timestamp':
        """Creates a Timestamp object with the current time."""
        return cls(datetime.now(timezone.utc))

    @classmethod
    def fromisoformat(cls, timestamp: str) -> 'Timestamp':
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
        return self.timestamp.isoformat().replace('+00:00', 'Z')

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Timestamp):
            return False
        return self.timestamp == value.timestamp

    @property
    def value(self) -> datetime:
        """Returns the timestamp value."""
        return self.timestamp


class Ciphertext(bytes):
    """Holds the encrypted value of an 'Entry'."""

    def __new__(cls, value: bytes):
        return super().__new__(cls, value)

    @classmethod
    def from_base64(cls, value: str) -> 'Ciphertext':
        """Creates a Ciphertext object from a base64 encoded string.

        Args:
            value: The base64 encoded string.

        Returns:
            The Ciphertext object.

        Raises:
            ValueError: If the value is not a valid base64 encoded string.
        """
        try:
            return cls(base64.b64decode(value.encode('ascii')))
        except binascii.Error as exc:
            raise ValueError("Invalid base64 string") from exc

    def to_base64(self) -> str:
        """Encodes the Ciphertext object as a base64 string.

        Returns:
            The base64 encoded string.
        """
        return base64.b64encode(self).decode('ascii')


class Plaintext(str):
    """Holds a plaintext value."""

    def __new__(cls, value: str) -> 'Plaintext':
        return super().__new__(cls, value)

    # pylint: disable=too-many-arguments
    @classmethod
    def random(
        cls,
        length: int,
        use_lowercase: bool = True,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_punctuation: bool = False,
    ) -> 'Plaintext':
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
        chars = ""
        if use_lowercase:
            chars += string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_digits:
            chars += string.digits
        if use_punctuation:
            chars += string.punctuation

        return cls(''.join(secrets.choice(chars) for _ in range(length)))


class EntryDict(TypedDict):
    """An 'Entry' represented as a dictionary."""

    id: str
    key_id: str
    timestamp: str
    description: str
    identity: Optional[str]
    ciphertext: str
    meta: Optional[str]


class Entry:
    """A record that stores an encrypted value along with associated information.

    Attributes:
        id: Uniquely identifies the entry.
        key_id: Represents the GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        ciphertext: Holds the encrypted value of the entry.
        meta: Optional field for additional non-specific information.
    """

    entry_id: EntryId
    key_id: KeyId
    timestamp: Timestamp
    description: Description
    identity: Optional[Identity]
    ciphertext: Ciphertext
    meta: Optional[Metadata]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        entry_id: EntryId,
        key_id: KeyId,
        timestamp: Timestamp,
        description: Description,
        identity: Optional[Identity],
        ciphertext: Ciphertext,
        meta: Optional[Metadata],
    ):
        self.entry_id = entry_id
        self.key_id = key_id
        self.timestamp = timestamp
        self.description = description
        self.identity = identity
        self.ciphertext = ciphertext
        self.meta = meta

    def __hash__(self) -> int:
        return hash(self.entry_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entry):
            return NotImplemented
        return (
            self.timestamp == other.timestamp
            and self.entry_id == other.entry_id
            and self.key_id == other.key_id
            and self.description == other.description
            and self.identity == other.identity
            and self.ciphertext == other.ciphertext
            and self.meta == other.meta
        )

    @classmethod
    def from_dict(cls, data: EntryDict) -> 'Entry':
        """Creates an 'Entry' from a dictionary.

        Args:
            data: The dictionary to create the 'Entry' from.

        Returns:
            The created 'Entry'.
        """
        # Check required keys
        check_keys = {'id', 'key_id', 'timestamp', 'description', 'ciphertext'}
        for key in check_keys:
            if key not in data:
                raise ValueError(f'Invalid entry format: missing required key "{key}"')

        # Validate the timestamp
        timestamp_str = data['timestamp']
        try:
            timestamp = Timestamp.fromisoformat(timestamp_str)
        except ValueError as err:
            raise ValueError('Invalid timestamp format') from err

        # Validate the ciphertext
        ciphertext_str = data['ciphertext']
        try:
            ciphertext = Ciphertext.from_base64(ciphertext_str)
        except ValueError as err:
            raise ValueError('Invalid ciphertext format') from err

        maybe_identity = data.get('identity')
        maybe_meta = data.get('meta')

        return cls(
            entry_id=EntryId(data['id']),
            key_id=KeyId(data['key_id']),
            timestamp=timestamp,
            description=Description(data['description']),
            identity=Identity(maybe_identity) if maybe_identity else None,
            ciphertext=ciphertext,
            meta=Metadata(maybe_meta) if maybe_meta else None,
        )

    def to_dict(self) -> EntryDict:
        """Converts the 'Entry' to a dictionary.

        Returns:
            The converted 'Entry'.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'id': self.entry_id,
            'key_id': self.key_id,
            'description': self.description,
            'identity': self.identity,
            'ciphertext': self.ciphertext.to_base64(),
            'meta': self.meta,
        }


def convert_to_snake(name: str) -> str:
    """Converts a string from CamelCase or snake_case to snake_case.

    Args:
        name: The string to convert.

    Returns:
        The converted string in snake_case.
    """
    underscore_inserted = re.sub('(.)([A-Z][a-z]*)', r'\1_\2', name)
    return re.sub('([a-z0-9A-Z])([A-Z])', r'\1_\2', underscore_inserted).lower()


def keys_to_snake_case(input_dict: Dict[Any, Any]) -> Dict[Any, Any]:
    """Converts all keys in a dictionary from CamelCase or snake_case to snake_case.

    Args:
        d: The dictionary to convert.

    Returns:
        A new dictionary with all keys converted to snake_case.
    """
    return {convert_to_snake(k): v for k, v in input_dict.items()}
