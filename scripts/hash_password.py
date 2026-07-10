"""Erzeugt den AECT_ADMIN_PASSWORD_HASH-Env-Wert fuer den Admin-Login.

Fragt das Passwort interaktiv ab (getpass -- kein Echo, keine Shell-History)
und gibt den fertigen Env-Wert `scrypt$<salt>$<hash>` aus. Das Klartext-Passwort
verlaesst den Prozess nie.

Nutzung:

    uv run python scripts/hash_password.py

Danach den ausgegebenen Wert in die lokale Env (z. B. .env, NICHT committen)
uebernehmen:

    AECT_ADMIN_PASSWORD_HASH=scrypt$...$...
"""

from __future__ import annotations

import getpass
import sys

from aect.adapters.api.password import hash_password


def main() -> int:
    password = getpass.getpass("Admin-Passwort: ")
    if not password:
        print("Abbruch: leeres Passwort.", file=sys.stderr)
        return 1
    confirm = getpass.getpass("Wiederholen: ")
    if password != confirm:
        print("Abbruch: Passwoerter stimmen nicht ueberein.", file=sys.stderr)
        return 1

    encoded = hash_password(password)
    print()
    print("AECT_ADMIN_PASSWORD_HASH in die lokale Env eintragen (nicht committen):")
    print()
    print(f"AECT_ADMIN_PASSWORD_HASH={encoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
