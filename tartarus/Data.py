from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Optional

Id = NewType('Id', str)
"""Uniquely identifies an 'Entry'."""

KeyId = NewType('KeyId', str)
"""Represents a GPG Key Id."""

Description = NewType('Description', str)
"""Describes an 'Entry'. Can be a URI or a descriptive name."""

Identity = NewType('Identity', str)
"""Represents an identifying value, such as the username in a username/password pair."""

Ciphertext = NewType('Ciphertext', bytes)
"""Holds the encrypted value of an 'Entry'."""

Metadata = NewType('Metadata', str)
"""Contains additional non-specific information for an 'Entry'."""


@dataclass
class Entry:
    """
    A record that stores an encrypted value along with associated information.

    Attributes:
        id: Uniquely identifies the entry.
        key_id: Represents the GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        ciphertext: Holds the encrypted value of the entry.
        meta: Optional field for additional non-specific information.
    """

    id: Id
    key_id: KeyId
    timestamp: datetime
    description: Description
    identity: Optional[Identity]
    ciphertext: Ciphertext
    meta: Optional[Metadata]
