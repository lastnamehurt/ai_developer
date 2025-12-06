"""
Encryption helpers for storing secrets in .env files.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover - defensive
    Fernet = None  # type: ignore

from aidev.constants import AIDEV_DIR
from aidev.utils import ensure_dir, console

ENV_KEY_FILE = AIDEV_DIR / ".env.key"
ENC_PREFIX = "ENC::"


def _load_or_create_key(key_path: Optional[Path] = None) -> bytes:
    """Load or create the symmetric key used for env encryption."""
    if Fernet is None:  # pragma: no cover - defensive
        raise RuntimeError("cryptography is required for encrypted env; please install it.")
    key_file = key_path or ENV_KEY_FILE
    if key_file.exists():
        return key_file.read_bytes()

    ensure_dir(key_file.parent)
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    try:
        os.chmod(key_file, 0o600)
    except Exception:
        # Best-effort permissions
        pass
    return key


def unlock_env_key(key_path: Optional[Path] = None) -> Path:
    """Ensure the env encryption key exists and return its path."""
    _load_or_create_key(key_path)
    return key_path or ENV_KEY_FILE


def encrypt_value(value: str, key_path: Optional[Path] = None) -> str:
    """Encrypt a value and return prefixed token."""
    key = _load_or_create_key(key_path)
    token = Fernet(key).encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{ENC_PREFIX}{token}"


def decrypt_value(value: str, key_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Attempt to decrypt a value if it is encrypted.

    Returns (is_encrypted, plaintext_or_original).
    """
    if not value.startswith(ENC_PREFIX):
        return False, value

    token = value[len(ENC_PREFIX) :]
    try:
        key = _load_or_create_key(key_path)
        plaintext = Fernet(key).decrypt(token.encode("utf-8")).decode("utf-8")
        return True, plaintext
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]Failed to decrypt secret: {exc}[/red]")
        return True, value
