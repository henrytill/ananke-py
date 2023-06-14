"""Core data structures and related functions."""
import base64
from datetime import datetime
from typing import NewType, Optional, TypedDict

KeyId = NewType('KeyId', str)
"""Represents a GPG Key Id."""

EntryId = NewType('EntryId', str)
"""Uniquely identifies an 'Entry'."""

Description = NewType('Description', str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType('Identity', str)
"""Represents an identifying value, such as the username in a username/password pair."""

Ciphertext = NewType('Ciphertext', bytes)
"""Holds the encrypted value of an 'Entry'."""

Plaintext = NewType('Plaintext', str)
"""Holds a plaintext value."""


Metadata = NewType('Metadata', str)
"""Contains additional non-specific information for an 'Entry'."""


def parse_timestamp(timestamp: str) -> datetime:
    """Parses a UTC ISO timestamp into a datetime object.

    Args:
        timestamp: The timestamp to parse.

    Returns:
        The parsed datetime object.

    Raises:
        ValueError: If the timestamp is in an invalid format.

    Examples:
        >>> parse_timestamp('2023-06-07T02:58:54.640805116Z')
        datetime.datetime(2023, 6, 7, 2, 58, 54, 640805)

        >>> parse_timestamp('2023-06-07T02:58:54Z')
        datetime.datetime(2023, 6, 7, 2, 58, 54)

        >>> parse_timestamp('2023-06-07T02:58Z')
        datetime.datetime(2023, 6, 7, 2, 58)
    """
    # Remove the Zulu indication
    timestamp = timestamp.rstrip('Z')

    # Separate date and time components
    date, time = timestamp.split('T')

    # Extract time components
    time_components = time.split(':')
    time_components_len = len(time_components)

    if time_components_len not in (2, 3):
        raise ValueError('Invalid timestamp format')

    # Extract time components and update the format string and timestamp_str incrementally
    hours = time_components[0]
    minutes = time_components[1]
    fmt = '%Y-%m-%dT%H:%M'
    timestamp_str = f'{date}T{hours}:{minutes}'

    if time_components_len == 3:  # seconds exist
        seconds = time_components[2]
        if '.' in seconds:
            # seconds include fractional part
            seconds_components = seconds.split('.')
            if len(seconds_components) != 2:
                raise ValueError('Invalid timestamp format')

            seconds = seconds_components[0]
            microseconds = seconds_components[1][:6]
            fmt += ':%S.%f'
            timestamp_str += f':{seconds}.{microseconds}'
        else:
            fmt += ':%S'
            timestamp_str += f':{seconds}'

    # Parse the timestamp string into a datetime object
    return datetime.strptime(timestamp_str, fmt)


class EntryDict(TypedDict):
    """An 'Entry' represented as a dictionary."""

    Id: str
    KeyId: str
    Timestamp: str
    Description: str
    Identity: Optional[str]
    Ciphertext: str
    Meta: Optional[str]


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
    timestamp: datetime
    description: Description
    identity: Optional[Identity]
    ciphertext: Ciphertext
    meta: Optional[Metadata]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        entry_id: EntryId,
        key_id: KeyId,
        timestamp: datetime,
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
        check_keys = {'Id', 'KeyId', 'Timestamp', 'Description', 'Ciphertext'}
        for key in check_keys:
            if key not in data:
                raise ValueError(f'Invalid entry format: missing required key "{key}"')

        # Validate the timestamp
        timestamp_str = data['Timestamp']
        try:
            timestamp = parse_timestamp(timestamp_str)
        except ValueError as err:
            raise ValueError('Invalid timestamp format') from err

        # Validate the ciphertext
        ciphertext_str = data['Ciphertext']
        try:
            ciphertext = base64.b64decode(ciphertext_str.encode(encoding='ascii'))
        except ValueError as err:
            raise ValueError('Invalid ciphertext format') from err

        maybe_identity = data.get('Identity')
        maybe_meta = data.get('Meta')

        return cls(
            entry_id=EntryId(data['Id']),
            key_id=KeyId(data['KeyId']),
            timestamp=timestamp,
            description=Description(data['Description']),
            identity=Identity(maybe_identity) if maybe_identity else None,
            ciphertext=Ciphertext(ciphertext),
            meta=Metadata(maybe_meta) if maybe_meta else None,
        )

    def to_dict(self) -> EntryDict:
        """Converts the 'Entry' to a dictionary.

        Returns:
            The converted 'Entry'.
        """
        ciphertext: str = base64.b64encode(self.ciphertext).decode(encoding='ascii')
        return {
            'Timestamp': self.timestamp.isoformat(),
            'Id': self.entry_id,
            'KeyId': self.key_id,
            'Description': self.description,
            'Identity': self.identity,
            'Ciphertext': ciphertext,
            'Meta': self.meta,
        }
