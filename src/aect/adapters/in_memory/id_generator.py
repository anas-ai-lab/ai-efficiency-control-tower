"""UUIDGenerator -- implementiert IdGeneratorPort mit uuid4."""

from __future__ import annotations

import uuid


class UUIDGenerator:
    """Generiert kryptografisch zufaellige UUID4-basierte IDs.

    Implementiert IdGeneratorPort via strukturellem Subtyping.
    """

    def generate(self) -> str:
        return str(uuid.uuid4())
