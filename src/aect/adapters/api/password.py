"""Passwort-Hashing fuer den Admin-Login (V4-P-Auth, stdlib-only).

Kein neues Dependency (Vorgabe): scrypt kommt aus hashlib (stdlib). scrypt ist
ein speicher-hartes KDF -- ein Offline-Brute-Force gegen einen geleakten Hash
skaliert deutlich schlechter als bei einem reinen sha256(salt+pw).

Format (im Env-Wert AECT_ADMIN_PASSWORD_HASH abgelegt):

    scrypt$<salt_hex>$<hash_hex>

Parameter (fest, im Format nicht kodiert -- ein Single-User-Demo braucht keine
Parameter-Migration): n=2**14, r=8, p=1, dklen=64. Speicherbedarf ~16 MiB
(128 * r * n) -- maxmem wird grosszuegig ueber den OpenSSL-Default gesetzt,
damit strengere Builds nicht mit ValueError abbrechen.

Verifikation ueber hmac.compare_digest (konstante Laufzeit) -- kein
timing-basiertes Byte-fuer-Byte-Erraten (analog require_api_key in
dependencies.py).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_SCHEME = "scrypt"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 64
# Grosszuegiger maxmem-Guard (64 MiB) -- der tatsaechliche Bedarf liegt bei
# ~16 MiB; ein hoeherer Wert aendert den Hash nicht, verhindert aber ein
# ValueError auf Builds mit strengerem Default.
_MAXMEM = 64 * 1024 * 1024


def _derive(password: str, salt: bytes) -> bytes:
    """Leitet den scrypt-Key aus Passwort + Salt ab (feste Parameter)."""
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_DKLEN,
        maxmem=_MAXMEM,
    )


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Erzeugt den Env-Wert `scrypt$<salt_hex>$<hash_hex>` fuer ein Passwort.

    salt: nur fuer deterministische Tests injizierbar -- im Normalfall wird ein
    frischer 16-Byte-Zufallssalt (secrets.token_bytes) verwendet.
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    derived = _derive(password, salt)
    return f"{_SCHEME}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Prueft ein Passwort gegen einen `scrypt$salt$hash`-Env-Wert.

    Fail loud gegen Fehlkonfiguration: ein leerer oder formal kaputter
    encoded-Wert liefert schlicht False (kein Match), wirft aber keine
    Exception -- der Login-Endpoint uebersetzt "kein konfigurierter Hash"
    separat in eine 503 (Server nicht betriebsbereit), verwechselt das also
    nicht mit einem falschen Passwort (401).
    """
    parts = encoded.split("$")
    if len(parts) != 3:
        return False
    scheme, salt_hex, hash_hex = parts
    if scheme != _SCHEME:
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    derived = _derive(password, salt)
    return hmac.compare_digest(derived, expected)
