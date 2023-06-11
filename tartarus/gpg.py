import subprocess

from .data import Ciphertext, KeyId, Plaintext


def encrypt(key_id: KeyId, plaintext: Plaintext) -> Ciphertext:
    """
    Encrypts a Plaintext using GPG.
    """
    input: bytes = plaintext.encode('utf-8')
    cmd = ['gpg', '--batch', '--encrypt', '--recipient', key_id]
    output: bytes = subprocess.run(cmd, input=input, capture_output=True).stdout
    return Ciphertext(output)


def decrypt(ciphertext: Ciphertext) -> Plaintext:
    """
    Decrypts a CipherText using GPG.
    """
    cmd = ['gpg', '--batch', '--decrypt']
    result: bytes = subprocess.run(cmd, input=ciphertext, capture_output=True).stdout
    return Plaintext(result.decode('utf-8'))
