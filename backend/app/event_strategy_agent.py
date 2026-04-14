"""EventStrategyAgent: club + sponsor -> three structured event ideas (JSON)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import ValidationError

from app.config import settings
from app.schemas import (
    ClubProfile,
    EventStrategyAgentResponse,
    SponsorBrief,
)

SYSTEM_PROMPT = """You are a campus events strategist for student organizations.
Return ONLY valid JSON (no markdown, no prose outside JSON).

Output MUST match this exact shape:
{
  "ideas": [
    {
      "title": string,
      "summary": string,
      "rationale": string,
      "estimatedAttendees": number | null,
      "supportRequested": string[],
      "tags": string[] | null
    },
    ... exactly 3 objects ...
  ]
}

Rules:
- Produce exactly three distinct, realistic events that align BOTH the club profile and the sponsor's mission and support types.
- Be specific (format, audience, timing hints) but do not invent legal commitments.
- supportRequested should list concrete asks (e.g. food budget, venue, swag, judges, API credits).
"""


def _call_llm(user_prompt: str) -> str:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured.",
        )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.35,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Model returned empty content.")
    return content


def generate_event_strategies(club: ClubProfile, sponsor: SponsorBrief) -> EventStrategyAgentResponse:
    user_prompt = (
        "Generate three event ideas for this pairing.\n\n"
        f"CLUB PROFILE JSON:\n{club.model_dump_json(by_alias=True)}\n\n"
        f"SPONSOR CONTEXT JSON:\n{sponsor.model_dump_json(by_alias=True)}\n"
    )

    first_output = _call_llm(user_prompt)
    try:
        data: Any = json.loads(first_output)
        return EventStrategyAgentResponse.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as first_error:
        fix_prompt = (
            "Your previous JSON was invalid for the required schema (exactly 3 ideas).\n"
            "Return ONLY corrected JSON.\n\n"
            f"ORIGINAL TASK:\n{user_prompt}\n\n"
            f"INVALID OUTPUT:\n{first_output}\n\n"
            f"ERROR:\n{first_error}\n"
        )
        second_output = _call_llm(fix_prompt)
        try:
            data2: Any = json.loads(second_output)
            return EventStrategyAgentResponse.model_validate(data2)
        except (json.JSONDecodeError, ValidationError) as second_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"EventStrategyAgent failed to return valid JSON: {second_error}",
            ) from second_error
