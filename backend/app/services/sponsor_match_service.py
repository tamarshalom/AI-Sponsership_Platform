"""
Sponsor matching v2: vector search + lightweight rule boost + LLM rerank.

Pipeline:
1) Embed club profile and fetch top-K sponsors by pgvector cosine search
2) Apply deterministic overlap boost (industries/support types)
3) LLM rerank to produce top-N with reasons + suggested activation
"""

from __future__ import annotations

import json
import logging
from textwrap import dedent

from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import ClubProfile, MatchSponsorsResponse, MatchSponsorsResult
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

VECTOR_TOP_K = 15
DEFAULT_FINAL_TOP_N = 5


def club_profile_to_match_text(club: ClubProfile) -> str:
    parts = [
        f"Club Name: {club.name}",
        f"Mission: {club.mission}",
    ]
    if club.description:
        parts.append(f"Description: {club.description}")
    if club.university:
        parts.append(f"University: {club.university}")
    if club.preferred_industries:
        parts.append(f"Preferred Industries: {', '.join(club.preferred_industries)}")
    if club.requested_support_types:
        parts.append(f"Requested Support Types: {', '.join(club.requested_support_types)}")
    if club.member_count:
        parts.append(f"Member Count: {club.member_count}")
    return "\n".join(parts)


def _as_list(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            return []
    return []


def _vector_search(
    session: Session,
    query_vector: str,
    *,
    top_k: int,
) -> list[dict]:
    stmt = text(
        """
        SELECT
            id AS sponsor_id,
            name AS sponsor_name,
            mission,
            description,
            industries,
            support_types,
            budget_min_cents,
            budget_max_cents,
            website_url,
            locations,
            1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
        FROM sponsors
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """
    )
    rows = (
        session.execute(stmt, {"query_embedding": query_vector, "limit": top_k})
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _compute_rule_boost(club: ClubProfile, sponsor: dict) -> float:
    """Deterministic bonus (0..0.15) for explicit field overlap."""
    boost = 0.0

    club_industries = {i.lower().replace(" ", "_") for i in (club.preferred_industries or [])}
    sponsor_industries = {i.lower().replace(" ", "_") for i in _as_list(sponsor.get("industries"))}
    overlap = club_industries & sponsor_industries
    if overlap:
        boost += min(len(overlap) * 0.03, 0.09)

    club_support = {s.lower().replace(" ", "_") for s in (club.requested_support_types or [])}
    sponsor_support = {s.lower().replace(" ", "_") for s in _as_list(sponsor.get("support_types"))}
    support_overlap = club_support & sponsor_support
    if support_overlap:
        boost += min(len(support_overlap) * 0.02, 0.06)

    return min(boost, 0.15)


RERANK_SYSTEM_PROMPT = dedent(
    """\
    You are an expert at matching corporate sponsors with university student clubs.
    You will receive a club profile and candidate sponsors.

    Return ONLY valid JSON:
    {
      "top_5": [
        {
          "sponsor_id": "exact candidate ID",
          "sponsor_name": "name",
          "score": 0.0-1.0,
          "mission": "mission",
          "description": "description",
          "reasons": ["2-4 short reasons"],
          "suggested_activation": "one concrete activation idea"
        }
      ]
    }
    """
)


def _build_rerank_prompt(club_text: str, candidates: list[dict]) -> str:
    blocks: list[str] = []
    for i, c in enumerate(candidates, 1):
        industries = _as_list(c.get("industries"))
        support = _as_list(c.get("support_types"))
        block = (
            f"[{i}] ID: {c['sponsor_id']} | {c['sponsor_name']}\n"
            f"  Mission: {c.get('mission', 'N/A')}\n"
            f"  Description: {c.get('description', 'N/A')}\n"
            f"  Industries: {', '.join(industries) if industries else 'N/A'}\n"
            f"  Support types: {', '.join(support) if support else 'N/A'}\n"
            f"  Vector score: {c.get('score', 0):.4f}\n"
            f"  Boosted score: {c.get('boosted_score', c.get('score', 0)):.4f}"
        )
        blocks.append(block)
    return (
        f"=== CLUB PROFILE ===\n{club_text}\n\n"
        f"=== CANDIDATE SPONSORS ({len(candidates)}) ===\n"
        + "\n\n".join(blocks)
    )


def _llm_rerank(club_text: str, candidates: list[dict], final_n: int) -> list[dict]:
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY missing; falling back to boosted vector ranking.")
        return candidates[:final_n]

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": RERANK_SYSTEM_PROMPT},
            {"role": "user", "content": _build_rerank_prompt(club_text, candidates)},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
        picks = data.get("top_5", [])
        if isinstance(picks, list):
            return picks[:final_n]
    except json.JSONDecodeError:
        logger.warning("Invalid rerank JSON; using boosted vector fallback.")

    return candidates[:final_n]


class SponsorMatchService:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embeddings = embedding_service or EmbeddingService()

    def match_top_sponsors(
        self,
        session: Session,
        club: ClubProfile,
        *,
        limit: int = DEFAULT_FINAL_TOP_N,
    ) -> MatchSponsorsResponse:
        club_text = club_profile_to_match_text(club)
        query_embedding = self._embeddings.create_embedding(club_text)
        query_vector = self._embeddings.to_pgvector_literal(query_embedding)
        candidates = _vector_search(session, query_vector, top_k=max(VECTOR_TOP_K, limit))
        if not candidates:
            return MatchSponsorsResponse(matches=[])

        for candidate in candidates:
            candidate["boosted_score"] = candidate.get("score", 0.0) + _compute_rule_boost(
                club, candidate
            )
        candidates.sort(key=lambda c: c.get("boosted_score", 0.0), reverse=True)

        picks = _llm_rerank(club_text, candidates, final_n=limit)

        matches: list[MatchSponsorsResult] = []
        for pick in picks:
            matches.append(
                MatchSponsorsResult(
                    sponsor_id=pick.get("sponsor_id", "unknown"),
                    sponsor_name=pick.get("sponsor_name", "Unknown"),
                    mission=pick.get("mission", ""),
                    description=pick.get("description"),
                    score=float(pick.get("score", pick.get("boosted_score", 0.0))),
                    reasons=pick.get("reasons"),
                    suggested_activation=pick.get("suggested_activation"),
                )
            )
        return MatchSponsorsResponse(matches=matches)
