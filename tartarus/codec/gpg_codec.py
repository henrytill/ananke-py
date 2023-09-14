"""The GpgCodec class."""
import subprocess

from ..data import Ciphertext, KeyId, Plaintext


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

    def encode(self, plaintext: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encode.

        Returns:
            The encoded Ciphertext.

        Raises:
            ValueError: If the Plaintext could not be encoded.
        """
        input_bytes = plaintext.encode("utf-8")
        cmd = ["gpg", "--batch", "--encrypt", "--recipient", self.key_id]
        try:
            output_bytes = subprocess.run(cmd, input=input_bytes, capture_output=True, check=True).stdout
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not encode Plaintext: {exc.stderr.decode("utf-8")}') from exc
        return Ciphertext(output_bytes)

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
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not decode Ciphertext: {exc.stderr.decode("utf-8")}') from exc
        return Plaintext(output_bytes.decode("utf-8"))
