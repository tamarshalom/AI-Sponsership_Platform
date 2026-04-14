"""
Sponsor Match Service (v2)
==========================
Pipeline:  embed club → pgvector top-K → rule-based boost → LLM rerank → top 5

Replaces the basic cosine-only matcher with a 3-stage pipeline.
Uses sync SQLAlchemy + sync OpenAI calls to match the existing codebase.
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
FINAL_TOP_N = 5
RERANK_MODEL = "gpt-4o-mini"


# ================================================================
#  Stage 1: Build club embedding text
# ================================================================

def club_profile_to_match_text(club: ClubProfile) -> str:
    """Build text for embedding — includes all relevant club fields."""
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


# ================================================================
#  Stage 2: Vector search (pgvector cosine)
# ================================================================

def vector_search(
    session: Session,
    query_vector: str,
    top_k: int = VECTOR_TOP_K,
) -> list[dict]:
    """
    Return top_k sponsors by cosine similarity.
    Uses the IVFFlat index from migration 0002.
    """
    stmt = text("""
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
    """)
    rows = (
        session.execute(stmt, {"query_embedding": query_vector, "limit": top_k})
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


# ================================================================
#  Stage 3: Rule-based boost
# ================================================================

def compute_rule_boost(club: ClubProfile, sponsor: dict) -> float:
    """
    Return a bonus (0 to 0.15) based on explicit field overlap:
    - industry match between club.preferred_industries and sponsor.industries
    - support type match
    """
    boost = 0.0

    # Industry overlap
    club_industries = {i.lower().replace(" ", "_") for i in (club.preferred_industries or [])}
    sponsor_industries = set()
    raw = sponsor.get("industries")
    if isinstance(raw, list):
        sponsor_industries = {i.lower().replace(" ", "_") for i in raw}
    elif isinstance(raw, str):
        try:
            sponsor_industries = {i.lower().replace(" ", "_") for i in json.loads(raw)}
        except (json.JSONDecodeError, TypeError):
            pass

    overlap = club_industries & sponsor_industries
    if overlap:
        boost += min(len(overlap) * 0.03, 0.09)

    # Support type overlap
    club_support = {s.lower().replace(" ", "_") for s in (club.requested_support_types or [])}
    sponsor_support = set()
    raw_st = sponsor.get("support_types")
    if isinstance(raw_st, list):
        sponsor_support = {s.lower().replace(" ", "_") for s in raw_st}
    elif isinstance(raw_st, str):
        try:
            sponsor_support = {s.lower().replace(" ", "_") for s in json.loads(raw_st)}
        except (json.JSONDecodeError, TypeError):
            pass

    support_overlap = club_support & sponsor_support
    if support_overlap:
        boost += min(len(support_overlap) * 0.02, 0.06)

    return min(boost, 0.15)


# ================================================================
#  Stage 4: LLM Rerank + Explain
# ================================================================

RERANK_SYSTEM_PROMPT = dedent("""\
You are an expert at matching corporate sponsors with university student clubs.

You will receive:
1. A CLUB PROFILE with their mission, preferred industries, and support needs.
2. A list of CANDIDATE SPONSORS with descriptions.

Your job:
- Pick the TOP 5 best-fitting sponsors from the candidates.
- For each, provide:
  - sponsor_id: the exact ID from the candidate list
  - sponsor_name: company name
  - score: match score from 0.0 to 1.0 (1.0 = perfect fit)
  - mission: the sponsor's mission
  - description: the sponsor's description
  - reasons: 2-4 short bullet points explaining WHY this sponsor fits this specific club
  - suggested_activation: one concrete idea for how the club could work with this sponsor

Respond ONLY with valid JSON. No markdown, no explanation outside JSON.
Format:
{
  "top_5": [
    {
      "sponsor_id": "sp_...",
      "sponsor_name": "...",
      "score": 0.85,
      "mission": "...",
      "description": "...",
      "reasons": ["reason1", "reason2"],
      "suggested_activation": "..."
    }
  ]
}

Scoring guidance:
- 0.90-1.0: near-perfect audience + mission alignment
- 0.75-0.89: strong fit with clear overlap
- 0.60-0.74: decent fit, some alignment
- below 0.60: weak fit
""")


def _build_rerank_prompt(club_text: str, candidates: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(candidates, 1):
        industries = c.get("industries", [])
        if isinstance(industries, str):
            try:
                industries = json.loads(industries)
            except (json.JSONDecodeError, TypeError):
                industries = []

        support = c.get("support_types", [])
        if isinstance(support, str):
            try:
                support = json.loads(support)
            except (json.JSONDecodeError, TypeError):
                support = []

        block = (
            f"[{i}] ID: {c['sponsor_id']} | {c['sponsor_name']}\n"
            f"  Mission: {c.get('mission', 'N/A')}\n"
            f"  Description: {c.get('description', 'N/A')}\n"
            f"  Industries: {', '.join(industries) if industries else 'N/A'}\n"
            f"  Support types: {', '.join(support) if support else 'N/A'}\n"
            f"  Budget: ${(c.get('budget_min_cents') or 0) / 100:.0f} - ${(c.get('budget_max_cents') or 0) / 100:.0f}"
        )
        blocks.append(block)

    return (
        f"=== CLUB PROFILE ===\n{club_text}\n\n"
        f"=== CANDIDATE SPONSORS ({len(candidates)}) ===\n"
        + "\n\n".join(blocks)
    )


def llm_rerank(club_text: str, candidates: list[dict]) -> list[dict]:
    """Call GPT-4o-mini to pick top 5 and explain each match."""
    client = OpenAI(api_key=settings.openai_api_key)
    user_msg = _build_rerank_prompt(club_text, candidates)

    response = client.chat.completions.create(
        model=RERANK_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": RERANK_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM rerank returned invalid JSON: %s", raw[:500])
        # Fallback: return top candidates as-is
        return [
            {
                "sponsor_id": c["sponsor_id"],
                "sponsor_name": c["sponsor_name"],
                "score": c.get("boosted_score", c["score"]),
                "mission": c.get("mission", ""),
                "description": c.get("description", ""),
            }
            for c in candidates[:FINAL_TOP_N]
        ]

    return data.get("top_5", [])[:FINAL_TOP_N]


# ================================================================
#  Main service class
# ================================================================

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
        """
        Full pipeline: embed → vector search → rule boost → LLM rerank → top 5.
        """
        # 1. Build club text & embed
        club_text = club_profile_to_match_text(club)
        query_embedding = self._embeddings.create_embedding(club_text)
        query_vector = self._embeddings.to_pgvector_literal(query_embedding)

        # 2. Vector search — get top 15
        candidates = vector_search(session, query_vector, VECTOR_TOP_K)

        if not candidates:
            return MatchSponsorsResponse(matches=[])

        # 3. Rule-based boost
        for c in candidates:
            boost = compute_rule_boost(club, c)
            c["boosted_score"] = c["score"] + boost

        candidates.sort(key=lambda x: x["boosted_score"], reverse=True)

        # 4. LLM rerank — get top 5 with reasoning
        reranked = llm_rerank(club_text, candidates)

        # 5. Build response using existing schema
        matches = []
        for pick in reranked:
            matches.append(
                MatchSponsorsResult(
                    sponsor_id=pick.get("sponsor_id", "unknown"),
                    sponsor_name=pick.get("sponsor_name", "Unknown"),
                    score=pick.get("score", 0.7),
                    mission=pick.get("mission", ""),
                    description=pick.get("description", ""),
                    # Extra fields the LLM returns — stored in the model if schema supports it
                    reasons=pick.get("reasons"),
                    suggested_activation=pick.get("suggested_activation"),
                )
            )

        return MatchSponsorsResponse(matches=matches)
