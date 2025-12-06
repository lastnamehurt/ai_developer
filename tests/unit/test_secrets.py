from pathlib import Path

import pytest

from aidev.secrets import Fernet, decrypt_value, encrypt_value, unlock_env_key


@pytest.mark.skipif(Fernet is None, reason="cryptography not installed")
def test_encrypt_decrypt_roundtrip(tmp_path: Path) -> None:
    key_path = tmp_path / "env.key"
    ciphertext = encrypt_value("super-secret", key_path=key_path)
    assert ciphertext.startswith("ENC::")

    is_enc, plaintext = decrypt_value(ciphertext, key_path=key_path)
    assert is_enc
    assert plaintext == "super-secret"


@pytest.mark.skipif(Fernet is None, reason="cryptography not installed")
def test_unlock_creates_key(tmp_path: Path) -> None:
    key_path = tmp_path / "custom.key"
    assert not key_path.exists()
    created = unlock_env_key(key_path=key_path)
    assert created == key_path
    assert key_path.exists()
    assert key_path.stat().st_size > 0
