import subprocess
from typing import Optional

from ..data import Ciphertext, KeyId, Plaintext
from .common import Cipher


class Binary(Cipher[Ciphertext]):
    """A GPG cipher.

    This class is used to encode Plaintexts and decode Ciphertexts using GPG.

    Attributes:
        key_id: The KeyId to use for encryption and decryption.
    """

    def __init__(self, key_id: KeyId) -> None:
        """Creates a new Binary encrypt with the given KeyId.

        Args:
            key_id: The KeyId to use for encryption and decryption.
        """
        self.key_id = key_id

    def encrypt(self, obj: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encrypt.

        Returns:
            The encrypted Ciphertext.

        Raises:
            ValueError: If the Plaintext could not be encrypted.
        """
        input_bytes = obj.encode("utf-8")
        cmd = ["gpg", "--batch", "--encrypt", "--recipient", self.key_id]
        try:
            output_bytes = subprocess.run(cmd, input=input_bytes, capture_output=True, check=True).stdout
            return Ciphertext(output_bytes)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not encrypt Plaintext: {exc.stderr.decode("utf-8")}') from exc

    def decrypt(self, ciphertext: Ciphertext) -> Plaintext:
        """Decodes a Ciphertext into a Plaintext.

        Args:
            ciphertext: The Ciphertext to decrypt.

        Returns:
            The decrypted Plaintext.

        Raises:
            ValueError: If the Ciphertext could not be decrypted.
        """
        cmd = ["gpg", "--batch", "--decrypt"]
        try:
            output_bytes = subprocess.run(cmd, input=ciphertext, capture_output=True, check=True).stdout
            return Plaintext(output_bytes.decode("utf-8"))
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not decrypt Ciphertext: {exc.stderr.decode("utf-8")}') from exc

    @staticmethod
    def suggest_key() -> Optional[KeyId]:
        """Suggests a `KeyId`"""
        try:
            # Try getting default public key
            # https://lists.gnupg.org/pipermail/gnupg-devel/2011-November/026308.html
            cmd = ["gpgconf", "--list-options", "gpg"]
            output = subprocess.run(cmd, capture_output=True, check=True, text=True).stdout
            for line in output.splitlines():
                fields = line.split(":")
                if fields[0] == "default-key":
                    key = fields[9][1:]
                    if len(key) != 0:
                        return KeyId(key)
                    break
            # Fall back to getting first public key listed
            cmd = ["gpg", "-k", "--with-colons"]
            output = subprocess.run(cmd, capture_output=True, check=True, text=True).stdout
            for line in output.splitlines():
                fields = line.split(":")
                if fields[0] == "pub":
                    key = fields[4][-8:]
                    if len(key) != 0:
                        return KeyId(key)
                    break
            # No suitable candidate found
            return None
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Failure occured trying to find a key: {exc.stderr.decode("utf-8")}') from exc
