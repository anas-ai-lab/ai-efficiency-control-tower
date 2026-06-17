"""Port-Protokolle (typing.Protocol) fuer den Application Service."""

from aect.application.ports.clock import ClockPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.llm import LLMMessage, LLMPort, LLMResponse
from aect.application.ports.repository import RepositoryPort
from aect.application.ports.retriever import RetrievedChunk, RetrieverPort

__all__ = [
    "ClockPort",
    "IdGeneratorPort",
    "LLMMessage",
    "LLMPort",
    "LLMResponse",
    "RepositoryPort",
    "RetrievedChunk",
    "RetrieverPort",
]
