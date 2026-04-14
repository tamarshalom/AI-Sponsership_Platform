"""Vector similarity search for sponsors using pgvector cosine distance (<=>)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import ClubProfile, MatchSponsorsResponse, MatchSponsorsResult
from app.services.embedding_service import EmbeddingService


def club_profile_to_match_text(club: ClubProfile) -> str:
    return (
        f"Club Name: {club.name}\n"
        f"Mission: {club.mission}\n"
        f"Description: {club.description or ''}\n"
        f"Preferred Industries: {', '.join(club.preferred_industries)}\n"
        f"Requested Support Types: {', '.join(club.requested_support_types)}\n"
    )


class SponsorMatchService:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embeddings = embedding_service or EmbeddingService()

    def match_top_sponsors(
        self,
        session: Session,
        club: ClubProfile,
        *,
        limit: int = 5,
    ) -> MatchSponsorsResponse:
        club_text = club_profile_to_match_text(club)
        query_embedding = self._embeddings.create_embedding(club_text)
        query_vector = self._embeddings.to_pgvector_literal(query_embedding)

        stmt = text(
            """
            SELECT
                id AS sponsor_id,
                name AS sponsor_name,
                mission,
                description,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM sponsors
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :limit
            """
        )
        rows = (
            session.execute(
                stmt,
                {"query_embedding": query_vector, "limit": limit},
            )
            .mappings()
            .all()
        )
        matches = [MatchSponsorsResult.model_validate(row) for row in rows]
        return MatchSponsorsResponse(matches=matches)
