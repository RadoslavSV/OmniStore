from __future__ import annotations

import hashlib
import hmac
import secrets


_ALGO = "sha256"
_ITERATIONS = 210_000  # добра стойност за PBKDF2 (можеш да я увеличиш по-късно)
_SALT_BYTES = 16
_KEY_LEN = 32


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")

    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS, dklen=_KEY_LEN)
    return f"pbkdf2_{_ALGO}${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iter_str, salt_hex, hash_hex = stored_hash.split("$", 3)
        if not scheme.startswith("pbkdf2_"):
            return False

        algo = scheme.replace("pbkdf2_", "")
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)

        dk = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, iterations, dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False
