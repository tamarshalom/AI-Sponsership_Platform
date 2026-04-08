"""OpenAI embedding generation and pgvector literal formatting."""

from __future__ import annotations

from fastapi import HTTPException, status
from openai import OpenAI

from app.config import settings


class EmbeddingService:
    """Wraps OpenAI embeddings API for club/sponsor text."""

    def create_embedding(self, text: str) -> list[float]:
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY is not configured.",
            )

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    @staticmethod
    def to_pgvector_literal(values: list[float]) -> str:
        """Format floats for SQL: CAST(:x AS vector)."""
        return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
