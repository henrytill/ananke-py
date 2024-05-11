import subprocess

from ..data import Ciphertext, KeyId, Plaintext
from .common import Codec


class GpgCodec(Codec[Plaintext]):
    """A GPG codec.

    This class is used to encode Plaintexts and decode Ciphertexts using GPG.

    Attributes:
        key_id: The KeyId to use for encryption and decryption.
    """

    def __init__(self, key_id: KeyId) -> None:
        """Creates a new GpgCodec with the given KeyId.

        Args:
            key_id: The KeyId to use for encryption and decryption.
        """
        self.key_id = key_id

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
