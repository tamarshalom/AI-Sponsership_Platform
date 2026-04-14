"""
Sponsor matching v2: vector retrieval + deterministic ranking + optional LLM explanations.
"""

from __future__ import annotations

import json
import logging
import re
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

CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "finance": {
        "finance",
        "fintech",
        "banking",
        "investment",
        "trading",
        "wall",
        "street",
        "consulting",
        "recruiting",
        "networking",
    },
    "health": {
        "health",
        "healthcare",
        "wellness",
        "medical",
        "public",
        "endometriosis",
        "reproductive",
        "mental",
        "clinic",
    },
    "business": {
        "business",
        "entrepreneurship",
        "startup",
        "marketing",
        "strategy",
        "product",
        "leadership",
        "operations",
    },
    "beauty": {
        "beauty",
        "cosmetics",
        "makeup",
        "skincare",
        "haircare",
        "fashion",
        "style",
    },
    "technology": {
        "ai",
        "software",
        "engineering",
        "cloud",
        "developer",
        "coding",
        "robotics",
        "data",
    },
}


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


def _mission_tokens(text: str) -> set[str]:
    parts = re.findall(r"[a-zA-Z]{4,}", text.lower())
    stop = {
        "club",
        "students",
        "student",
        "their",
        "with",
        "that",
        "from",
        "this",
        "about",
        "your",
        "into",
        "through",
        "support",
        "supports",
        "events",
        "event",
    }
    return {p for p in parts if p not in stop}


def _detect_club_categories(club: ClubProfile) -> set[str]:
    text = " ".join(
        part
        for part in [
            club.name,
            club.mission,
            club.description or "",
            " ".join(club.preferred_industries or []),
            " ".join(club.requested_support_types or []),
        ]
        if part
    ).lower()
    categories: set[str] = set()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            categories.add(category)
    return categories


def _detect_sponsor_categories(sponsor: dict) -> set[str]:
    text = " ".join(
        [
            str(sponsor.get("sponsor_name") or ""),
            str(sponsor.get("mission") or ""),
            str(sponsor.get("description") or ""),
            " ".join(_as_list(sponsor.get("industries"))),
            " ".join(_as_list(sponsor.get("support_types"))),
        ]
    ).lower()
    categories: set[str] = set()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            categories.add(category)
    return categories


def _compute_rule_boost(club: ClubProfile, sponsor: dict) -> float:
    """Deterministic bonus (0..0.25) for overlap and mission keyword alignment."""
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

    club_text = " ".join(
        part
        for part in [
            club.mission,
            club.description or "",
            " ".join(club.preferred_industries or []),
            " ".join(club.requested_support_types or []),
        ]
        if part
    )
    sponsor_text = " ".join(
        part
        for part in [
            str(sponsor.get("mission") or ""),
            str(sponsor.get("description") or ""),
            " ".join(_as_list(sponsor.get("industries"))),
            " ".join(_as_list(sponsor.get("support_types"))),
        ]
        if part
    )
    token_overlap = _mission_tokens(club_text) & _mission_tokens(sponsor_text)
    if token_overlap:
        boost += min(len(token_overlap) * 0.01, 0.10)

    club_categories = _detect_club_categories(club)
    sponsor_categories = _detect_sponsor_categories(sponsor)
    if club_categories and sponsor_categories:
        category_overlap = club_categories & sponsor_categories
        if category_overlap:
            # Strong category routing signal for common club types.
            boost += min(0.12, 0.06 * len(category_overlap))
        else:
            # Slight penalty when no category alignment exists.
            boost -= 0.03

    return max(-0.05, min(boost, 0.35))


EXPLAIN_SYSTEM_PROMPT = dedent(
    """\
    You are an expert at matching corporate sponsors with university student clubs.
    You will receive a club profile and a fixed list of matched sponsors.

    Return ONLY valid JSON:
    {
      "explanations": [
        {
          "sponsor_id": "exact sponsor ID from the list",
          "reasons": ["2-4 short reasons"],
          "suggested_activation": "one concrete activation idea"
        }
      ]
    }

    Rules:
    - Do NOT invent sponsor IDs.
    - Do NOT reorder or score sponsors.
    - Keep reasons specific to the club mission.
    """
)


def _build_explain_prompt(club_text: str, candidates: list[dict]) -> str:
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


def _llm_enrich(club_text: str, candidates: list[dict], final_n: int) -> list[dict]:
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY missing; falling back to boosted vector ranking.")
        return candidates[:final_n]

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
                {"role": "user", "content": _build_explain_prompt(club_text, candidates)},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM enrich failed; using deterministic ranking only: %s", exc)
        return candidates[:final_n]

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
        explanations = data.get("explanations", [])
        if not isinstance(explanations, list):
            return candidates[:final_n]
        by_id: dict[str, dict] = {}
        for explanation in explanations:
            if not isinstance(explanation, dict):
                continue
            sponsor_id = explanation.get("sponsor_id")
            if isinstance(sponsor_id, str):
                by_id[sponsor_id] = explanation

        enriched: list[dict] = []
        for candidate in candidates[:final_n]:
            merged = dict(candidate)
            extra = by_id.get(str(candidate.get("sponsor_id")))
            if extra:
                merged["reasons"] = extra.get("reasons")
                merged["suggested_activation"] = extra.get("suggested_activation")
            enriched.append(merged)
        return enriched
    except json.JSONDecodeError:
        logger.warning("Invalid explanation JSON; using deterministic ranking only.")

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
        filtered = [
            c
            for c in candidates
            if float(c.get("boosted_score", 0.0)) >= settings.match_min_score
        ]
        # Keep quality filtering, but still provide enough options.
        if len(filtered) >= settings.match_min_results:
            candidates = filtered
        else:
            # Backfill from best unfiltered candidates to reach minimum shortlist size.
            target = max(settings.match_min_results, min(limit, len(candidates)))
            candidates = candidates[:target]

        finalists = candidates[:limit]
        picks = _llm_enrich(club_text, finalists, final_n=limit)

        matches: list[MatchSponsorsResult] = []
        for pick in picks:
            matches.append(
                MatchSponsorsResult(
                    sponsor_id=pick.get("sponsor_id", "unknown"),
                    sponsor_name=pick.get("sponsor_name", "Unknown"),
                    mission=pick.get("mission", ""),
                    description=pick.get("description"),
                    score=max(
                        0.0,
                        min(1.0, float(pick.get("boosted_score", pick.get("score", 0.0)))),
                    ),
                    reasons=pick.get("reasons"),
                    suggested_activation=pick.get("suggested_activation"),
                )
            )
        return MatchSponsorsResponse(matches=matches)
