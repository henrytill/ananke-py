"""Tests for the GpgCodec class."""
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from tartarus.codec import GpgCodec
from tartarus.data import Ciphertext, KeyId, Plaintext


class TestGpgCodec(unittest.TestCase):
    """Test cases for the GpgCodec class.

    These tests use the unittest.mock.patch function to replace the subprocess.run
    function with a mock, allowing the tests to run without actually invoking GPG.
    """

    @patch('subprocess.run')
    def test_encode(self, mock_run: MagicMock):
        """Tests the encode method.

        This test checks that the encode method correctly calls subprocess.run with the
        expected arguments and correctly creates a Ciphertext object from the output.
        """
        mock_run.return_value.stdout = b'encoded_text'

        codec = GpgCodec(KeyId('key_id'))
        result = codec.encode(Plaintext('hello'))

        self.assertEqual(result, Ciphertext(b'encoded_text'))
        mock_run.assert_called_once_with(
            ['gpg', '--batch', '--encrypt', '--recipient', 'key_id'], input=b'hello', capture_output=True, check=True
        )

    @patch('subprocess.run')
    def test_decode(self, mock_run: MagicMock):
        """Tests the decode method.

        This test checks that the decode method correctly calls subprocess.run with the
        expected arguments and correctly creates a Plaintext object from the output.
        """
        mock_run.return_value.stdout = b'decoded_text'

        codec = GpgCodec(KeyId('key_id'))
        result = codec.decode(Ciphertext(b'hello'))

        self.assertEqual(result, Plaintext('decoded_text'))
        mock_run.assert_called_once_with(
            ['gpg', '--batch', '--decrypt'], input=b'hello', capture_output=True, check=True
        )

    @patch('subprocess.run')
    def test_encode_failure(self, mock_run: MagicMock):
        """Tests the encode method when subprocess.run raises an exception.

        This test checks that the encode method raises a ValueError with the expected
        message when subprocess.run raises a CalledProcessError.
        """
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', stderr=b'error_message')

        codec = GpgCodec(KeyId('key_id'))
        with self.assertRaises(ValueError) as context:
            codec.encode(Plaintext('hello'))

        self.assertEqual(str(context.exception), 'Could not encode Plaintext: error_message')

    @patch('subprocess.run')
    def test_decode_failure(self, mock_run: MagicMock):
        """Tests the decode method when subprocess.run raises an exception.

        This test checks that the decode method raises a ValueError with the expected
        message when subprocess.run raises a CalledProcessError.
        """
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', stderr=b'error_message')

        codec = GpgCodec(KeyId('key_id'))
        with self.assertRaises(ValueError) as context:
            codec.decode(Ciphertext(b'hello'))

        self.assertEqual(str(context.exception), 'Could not decode Ciphertext: error_message')

    def test_key_id_getter(self) -> None:
        """Tests the key_id getter.

        This test checks that the getter of the key_id property returns the correct KeyId.
        """
        codec = GpgCodec(KeyId('original_key_id'))
        self.assertEqual(codec.key_id, KeyId('original_key_id'))

    def test_key_id_setter(self) -> None:
        """Tests the key_id setter.

        This test checks that the setter of the key_id property updates the KeyId correctly.
        """
        codec = GpgCodec(KeyId('original_key_id'))
        codec.key_id = KeyId('new_key_id')
        self.assertEqual(codec.key_id, KeyId('new_key_id'))


if __name__ == '__main__':
    unittest.main()
