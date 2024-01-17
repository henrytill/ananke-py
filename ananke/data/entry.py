"""Module for the 'Entry' class and related types."""
import base64
import binascii
import functools
import hashlib
import subprocess
from typing import Any, Optional, Self

from . import core
from .core import Description, Identity, KeyId, Metadata, Plaintext, Timestamp


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
        # Get required keys
        id_str: str = core.get_required(data, "id", str)
        key_id_str: str = core.get_required(data, "key_id", str)
        timestamp_str: str = core.get_required(data, "timestamp", str)
        description_str: str = core.get_required(data, "description", str)
        ciphertext_str: str = core.get_required(data, "ciphertext", str)

        # Get optional keys
        maybe_identity: Optional[str] = core.get_optional(data, "identity", str)
        maybe_meta: Optional[str] = core.get_optional(data, "meta", str)

        # Validate timestamp
        try:
            timestamp = Timestamp.fromisoformat(timestamp_str)
        except ValueError as err:
            raise ValueError("Invalid timestamp format") from err

        # Validate ciphertext
        try:
            ciphertext = Ciphertext.from_base64(ciphertext_str)
        except ValueError as err:
            raise ValueError("Invalid ciphertext format") from err

        return cls(
            entry_id=EntryId(id_str),
            key_id=KeyId(key_id_str),
            timestamp=timestamp,
            description=Description(description_str),
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


remap_keys_camel_to_snake = functools.partial(core.remap_keys, CAMEL_TO_SNAKE)
remap_keys_snake_to_camel = functools.partial(core.remap_keys, SNAKE_TO_CAMEL)


class GpgCodec:
    """A GPG codec.

    This class is used to encode Plaintexts and decode Ciphertexts using GPG.
    """

    _key_id: KeyId

    def __init__(self, key_id: KeyId) -> None:
        """Creates a new GpgCodec with the given KeyId.

        Args:
            key_id: The KeyId to use for encryption and decryption.
        """
        self._key_id = key_id

    @property
    def key_id(self) -> KeyId:
        """Returns the KeyId of this GpgCodec."""
        return self._key_id

    @key_id.setter
    def key_id(self, key_id: KeyId) -> None:
        self._key_id = key_id

    def encode(self, obj: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encode.

        Returns:
            The encoded Ciphertext.

        Raises:
            ValueError: If the Plaintext could not be encoded.
        """
        input_bytes = obj.encode("utf-8")
        cmd = ["gpg", "--batch", "--encrypt", "--recipient", self.key_id]
        try:
            output_bytes = subprocess.run(cmd, input=input_bytes, capture_output=True, check=True).stdout
            return Ciphertext(output_bytes)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not encode Plaintext: {exc.stderr.decode("utf-8")}') from exc

    def decode(self, ciphertext: Ciphertext) -> Plaintext:
        """Decodes a Ciphertext into a Plaintext.

        Args:
            ciphertext: The Ciphertext to decode.

        Returns:
            The decoded Plaintext.

        Raises:
            ValueError: If the Ciphertext could not be decoded.
        """
        cmd = ["gpg", "--batch", "--decrypt"]
        try:
            output_bytes = subprocess.run(cmd, input=ciphertext, capture_output=True, check=True).stdout
            return Plaintext(output_bytes.decode("utf-8"))
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not decode Ciphertext: {exc.stderr.decode("utf-8")}') from exc
