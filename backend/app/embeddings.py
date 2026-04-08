"""Backward-compatible helpers; prefer app.services.embedding_service.EmbeddingService."""

from __future__ import annotations

from app.services.embedding_service import EmbeddingService

_default = EmbeddingService()


def create_embedding(text: str) -> list[float]:
    return _default.create_embedding(text)


def vector_literal(values: list[float]) -> str:
    return _default.to_pgvector_literal(values)
