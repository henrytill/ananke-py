import subprocess
from typing import Optional

from .common import ArmoredCiphertext, Cipher, Ciphertext, KeyId, Plaintext


class Binary(Cipher[Ciphertext]):
    """A binary GPG cipher.

    This class is used to encode Plaintexts and decode Ciphertexts to/from binary using GPG.

    Attributes:
        key_id: The KeyId to use for encryption and decryption.
    """

    def __init__(self, key_id: KeyId) -> None:
        """Creates a new Binary with the given KeyId.

        Args:
            key_id: The KeyId to use for encryption and decryption.
        """
        self.key_id = key_id

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Binary):
            return False
        return self.key_id == value.key_id

    def encrypt(self, plaintext: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encrypt.

        Returns:
            The encrypted Ciphertext.

        Raises:
            ValueError: If the Plaintext could not be encrypted.
        """
        input_bytes = plaintext.encode("utf-8")
        cmd = ["gpg", "--batch", "--encrypt", "--recipient", self.key_id]
        try:
            output_bytes = subprocess.run(cmd, input=input_bytes, capture_output=True, check=True).stdout
            return Ciphertext(output_bytes)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not encrypt Plaintext: {exc.stderr.decode("utf-8")}') from exc

    def decrypt(self, obj: Ciphertext) -> Plaintext:
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
            output_bytes = subprocess.run(cmd, input=obj, capture_output=True, check=True).stdout
            return Plaintext(output_bytes.decode("utf-8"))
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not decrypt Ciphertext: {exc.stderr.decode("utf-8")}') from exc

    @staticmethod
    def suggest_key() -> Optional[KeyId]:
        """Suggests a KeyId"""
        return _suggest_key()


class Text(Cipher[ArmoredCiphertext]):
    """A text GPG cipher.

    This class is used to encode Plaintexts and decode Ciphertexts to/from ASCII-armored text using GPG.

    Attributes:
        key_id: The KeyId to use for encryption and decryption.
    """

    def __init__(self, key_id: KeyId) -> None:
        """Creates a new Text with the given KeyId.

        Args:
            key_id: The KeyId to use for encryption and decryption.
        """
        self.key_id = key_id

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Text):
            return False
        return self.key_id == value.key_id

    def encrypt(self, plaintext: Plaintext) -> ArmoredCiphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encrypt.

        Returns:
            The encrypted ArmoredCiphertext.

        Raises:
            ValueError: If the Plaintext could not be encrypted.
        """
        input_bytes = plaintext.encode("utf-8")
        cmd = ["gpg", "--batch", "--armor", "-q", "-e", "-r", self.key_id]
        try:
            output_bytes = subprocess.run(cmd, input=input_bytes, capture_output=True, check=True).stdout
            return ArmoredCiphertext(output_bytes.decode("utf-8"))
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not encrypt Plaintext: {exc.stderr.decode("utf-8")}') from exc

    def decrypt(self, obj: ArmoredCiphertext) -> Plaintext:
        """Decodes a Ciphertext into a Plaintext.

        Args:
            ciphertext: The ArmoredCiphertext to decrypt.

        Returns:
            The decrypted Plaintext.

        Raises:
            ValueError: If the ArmoredCiphertext could not be decrypted.
        """
        input_bytes = obj.encode("utf-8")
        cmd = ["gpg", "--batch", "-q", "-d"]
        try:
            output_bytes = subprocess.run(cmd, input=input_bytes, capture_output=True, check=True).stdout
            return Plaintext(output_bytes.decode("utf-8"))
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'Could not decrypt Ciphertext: {exc.stderr.decode("utf-8")}') from exc

    @staticmethod
    def suggest_key() -> Optional[KeyId]:
        """Suggests a KeyId"""
        return _suggest_key()


def _suggest_key() -> Optional[KeyId]:
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
