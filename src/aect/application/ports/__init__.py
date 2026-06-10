"""Port-Protokolle (typing.Protocol) fuer den Application Service."""

from aect.application.ports.clock import ClockPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.repository import RepositoryPort

__all__ = ["ClockPort", "IdGeneratorPort", "RepositoryPort"]
