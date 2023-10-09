"""Module for the 'Entry' class and related types."""
import base64
import binascii
import functools
import hashlib
from typing import Any, Optional, Self

from .core import Description, Identity, KeyId, Metadata, Timestamp, remap_keys


class EntryId(str):
    """Uniquely identifies an 'Entry'."""

    def __new__(cls, value: str) -> Self:
        return super().__new__(cls, value)

    @classmethod
    def generate(
        cls,
        key_id: KeyId,
        timestamp: Timestamp,
        description: Description,
        maybe_identity: Optional[Identity] = None,
    ) -> Self:
        """Generates an EntryId from the given values.

        Args:
            key_id: The GPG Key Id used for encryption.
            timestamp: The time the entry was created or updated.
            description: Description of the entry. Can be a URI or a descriptive name.
            maybe_identity: Optional identifying value, such as a username.

        Returns:
            The generated EntryId.
        """
        input_str = f"{key_id}{timestamp.isoformat()}{description}"
        if maybe_identity:
            input_str += maybe_identity
        sha_signature = hashlib.sha1(input_str.encode()).hexdigest()
        return cls(sha_signature)


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


class Entry:
    """A record that stores an encrypted value along with associated information.

    Attributes:
        entry_id: Uniquely identifies the entry.
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
    ) -> None:
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
    def from_dict(cls, data: dict[Any, Any]) -> Self:
        """Creates an 'Entry' from a dictionary.

        Args:
            data: The dictionary to create the 'Entry' from.

        Returns:
            The created 'Entry'.
        """
        # Check required keys
        required_keys = {
            "id": str,
            "key_id": str,
            "timestamp": str,
            "description": str,
            "ciphertext": str,
        }

        for key, value_type in required_keys.items():
            if key not in data:
                raise ValueError(f'Invalid entry format: missing required key "{key}"')
            if not isinstance(data[key], value_type):
                raise ValueError(f"Invalid {key} format")

        # Check optional keys
        optional_keys = {
            "identity": str,
            "meta": str,
        }

        for key, value_type in optional_keys.items():
            maybe_value = data.get(key)
            if maybe_value is None:
                continue
            if not isinstance(maybe_value, value_type):
                raise ValueError(f"Invalid {key} format")

        maybe_identity = data.get("identity")
        maybe_meta = data.get("meta")

        # Validate timestamp
        timestamp_str = data["timestamp"]
        try:
            timestamp = Timestamp.fromisoformat(timestamp_str)
        except ValueError as err:
            raise ValueError("Invalid timestamp format") from err

        # Validate ciphertext
        ciphertext_str = data["ciphertext"]
        try:
            ciphertext = Ciphertext.from_base64(ciphertext_str)
        except ValueError as err:
            raise ValueError("Invalid ciphertext format") from err

        return cls(
            entry_id=EntryId(data["id"]),
            key_id=KeyId(data["key_id"]),
            timestamp=timestamp,
            description=Description(data["description"]),
            identity=Identity(maybe_identity) if maybe_identity else None,
            ciphertext=ciphertext,
            meta=Metadata(maybe_meta) if maybe_meta else None,
        )

    def to_dict(self) -> dict[str, str]:
        """Converts the 'Entry' to a dictionary.

        Returns:
            The converted 'Entry'.
        """
        ret = {
            "timestamp": self.timestamp.isoformat(),
            "id": self.entry_id,
            "key_id": self.key_id,
            "description": self.description,
            "ciphertext": self.ciphertext.to_base64(),
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
    "ciphertext": "ciphertext",
    "meta": "meta",
    # PascalCase
    "Timestamp": "timestamp",
    "Id": "id",
    "KeyId": "key_id",
    "Description": "description",
    "Identity": "identity",
    "Ciphertext": "ciphertext",
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


remap_keys_camel_to_snake = functools.partial(remap_keys, CAMEL_TO_SNAKE)
remap_keys_snake_to_camel = functools.partial(remap_keys, SNAKE_TO_CAMEL)
