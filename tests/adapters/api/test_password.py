"""Unit-Tests fuer das scrypt-Passwort-Hashing (V4-P-Auth, stdlib-only)."""

from __future__ import annotations

from aect.adapters.api.password import hash_password, verify_password


def test_roundtrip_verifies() -> None:
    encoded = hash_password("korrektes-passwort")
    assert verify_password("korrektes-passwort", encoded) is True


def test_wrong_password_does_not_verify() -> None:
    encoded = hash_password("korrektes-passwort")
    assert verify_password("falsches-passwort", encoded) is False


def test_encoded_format_is_scrypt_salt_hash() -> None:
    encoded = hash_password("x")
    parts = encoded.split("$")
    assert parts[0] == "scrypt"
    assert len(parts) == 3
    # salt (16 Byte) und Hash (64 Byte) als Hex.
    assert len(parts[1]) == 32
    assert len(parts[2]) == 128


def test_same_password_different_salt_differs() -> None:
    a = hash_password("gleich")
    b = hash_password("gleich")
    assert a != b  # frischer Zufallssalt je Aufruf
    assert verify_password("gleich", a)
    assert verify_password("gleich", b)


def test_deterministic_with_fixed_salt() -> None:
    salt = b"0123456789abcdef"
    assert hash_password("pw", salt=salt) == hash_password("pw", salt=salt)


def test_malformed_encoded_returns_false() -> None:
    assert verify_password("pw", "") is False
    assert verify_password("pw", "notscrypt$aa$bb") is False
    assert verify_password("pw", "scrypt$only-two-parts") is False
    # Nicht-Hex im Salt/Hash -> False statt Exception.
    assert verify_password("pw", "scrypt$zz$zz") is False
