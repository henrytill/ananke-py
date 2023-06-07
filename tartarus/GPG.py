import base64
import subprocess

from tartarus.Data import Ciphertext, KeyId, Plaintext


class GPG:
    @staticmethod
    def encrypt(key_id: KeyId, plaintext: Plaintext) -> str:
        """
        Encrypts a Plaintext using GPG.
        """
        # Encode the plaintext
        plaintext = plaintext.encode('utf-8')
        # Encrypt the plaintext
        cmd = ['gpg', '--batch', '--encrypt', '--recipient', key_id]
        # Execute the command returning the ciphertext in bytes
        ciphertext = subprocess.run(cmd, input=plaintext, capture_output=True).stdout
        # Encode the ciphertext
        ciphertext = base64.b64encode(ciphertext).decode('utf-8')
        # Return the ciphertext
        return ciphertext

    @staticmethod
    def decrypt(ciphertext: Ciphertext) -> str:
        """
        Decrypts a CipherText using GPG.
        """
        # Decode the ciphertext
        ciphertext = base64.b64decode(ciphertext.encode('utf-8'))
        # Decrypt the ciphertext
        cmd = ['gpg', '--batch', '--decrypt']
        # Execute the command returning the plaintext in bytes
        plaintext = subprocess.run(cmd, input=ciphertext, capture_output=True).stdout
        # Decode the plaintext
        plaintext = plaintext.decode('utf-8')
        # Return the plaintext
        return plaintext
