"""Module for the 'SecureEntry' class and related types."""

# pylint: disable=duplicate-code
import functools
from typing import Any, Dict, NewType, Optional, Self
from uuid import UUID

from . import common
from .common import Description, EntryId, Identity, KeyId, Metadata, Plaintext, Timestamp

ArmoredCiphertext = NewType("ArmoredCiphertext", str)
"""An armored ciphertext value of an 'SecureEntry'."""


class SecureEntry:
    """A record that stores a plaintext value along with associated information.

    Attributes:
        entry_id: Uniquely identifies the entry.
        key_id: The GPG Key Id used for encryption.
        timestamp: The time the entry was created.
        description: Description of the entry. Can be a URI or a descriptive name.
        identity: Optional identifying value, such as a username.
        plaintext: The plaintext value.
        meta: Optional field for additional non-specific information.
    """

    entry_id: EntryId
    key_id: KeyId
    timestamp: Timestamp
    description: Description
    identity: Optional[Identity]
    plaintext: Plaintext
    meta: Optional[Metadata]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        entry_id: EntryId,
        key_id: KeyId,
        timestamp: Timestamp,
        description: Description,
        identity: Optional[Identity],
        plaintext: Plaintext,
        meta: Optional[Metadata],
    ) -> None:
        self.entry_id = entry_id
        self.key_id = key_id
        self.timestamp = timestamp
        self.description = description
        self.identity = identity
        self.plaintext = plaintext
        self.meta = meta

    def __repr__(self) -> str:
        return f"SecureEntry({self.entry_id})"

    def __hash__(self) -> int:
        return hash(self.entry_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecureEntry):
            return False
        return (
            self.timestamp == other.timestamp
            and self.entry_id == other.entry_id
            and self.key_id == other.key_id
            and self.description == other.description
            and self.identity == other.identity
            and self.plaintext == other.plaintext
            and self.meta == other.meta
        )

    @classmethod
    def from_dict(cls, data: Dict[Any, Any]) -> Self:
        """Creates a 'SecretEntry' from a dictionary.

        Args:
            data: The dictionary to create the 'SecretEntry' from.

        Returns:
            The created 'SecretEntry'.
        """
        # Get required keys
        id_str: str = common.get_required(data, "id", str)
        key_id_str: str = common.get_required(data, "key_id", str)
        timestamp_str = common.get_required(data, "timestamp", str)
        description_str = common.get_required(data, "description", str)
        plaintext_str = common.get_required(data, "plaintext", str)

        # Get optional keys
        maybe_identity = common.get_optional(data, "identity", str)
        maybe_meta = common.get_optional(data, "meta", str)

        # Validate entry id
        try:
            uuid = UUID(id_str)
        except ValueError as err:
            raise ValueError("Invalid id format") from err

        # Validate timestamp
        try:
            timestamp = Timestamp.fromisoformat(timestamp_str)
        except ValueError as err:
            raise ValueError("Invalid timestamp format") from err

        return cls(
            entry_id=EntryId(uuid),
            key_id=KeyId(key_id_str),
            timestamp=timestamp,
            description=Description(description_str),
            identity=Identity(maybe_identity) if maybe_identity else None,
            plaintext=Plaintext(plaintext_str),
            meta=Metadata(maybe_meta) if maybe_meta else None,
        )

    def to_dict(self) -> Dict[str, str]:
        """Converts the 'SecretEntry' to a dictionary.

        Returns:
            The converted 'SecretEntry'.
        """
        ret = {
            "timestamp": self.timestamp.isoformat(),
            "id": str(self.entry_id),
            "key_id": self.key_id,
            "description": self.description,
            "plaintext": str(self.plaintext),
        }
        if self.identity is not None:
            ret["identity"] = self.identity
        if self.meta is not None:
            ret["meta"] = self.meta
        return ret


CAMEL_TO_SNAKE = {
    # camelCase
    "timestamp": "timestamp",
    "id": "id",
    "keyId": "key_id",
    "description": "description",
    "identity": "identity",
    "plaintext": "plaintext",
    "meta": "meta",
    # PascalCase
    "Timestamp": "timestamp",
    "Id": "id",
    "KeyId": "key_id",
    "Description": "description",
    "Identity": "identity",
    "Plaintext": "plaintext",
    "Meta": "meta",
}

SNAKE_TO_CAMEL = {
    "timestamp": "timestamp",
    "id": "id",
    "key_id": "keyId",
    "description": "description",
    "identity": "identity",
    "ciphertext": "ciphertext",
    "meta": "meta",
}


remap_keys_camel_to_snake = functools.partial(common.remap_keys, CAMEL_TO_SNAKE)
remap_keys_snake_to_camel = functools.partial(common.remap_keys, SNAKE_TO_CAMEL)
