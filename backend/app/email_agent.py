"""EmailAgent: one event idea + club + sponsor -> sponsorship pitch (subject + body)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import ValidationError

from app.config import settings
from app.schemas import ClubProfile, EmailPitchResponse, EventStrategyIdea, SponsorBrief

SYSTEM_PROMPT = """You write outreach email drafts for student organizations seeking sponsorship.

Return ONLY valid JSON (no markdown) with this shape:
{ "subject": string, "body": string }

Tone (required): professional student leader — ambitious but organized.
- Clear structure (greeting, context, proposal, ask, appreciation, sign-off).
- Confident and specific; avoid slang; sound like a capable club officer, not a corporation.
- Do not invent binding commitments, dollar amounts you cannot justify, or fake prior conversations.
- Keep body concise: roughly 180–320 words unless the event clearly needs more.
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
        temperature=0.45,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Model returned empty content.")
    return content


def generate_sponsorship_pitch(
    club: ClubProfile,
    sponsor: SponsorBrief,
    event_idea: EventStrategyIdea,
) -> EmailPitchResponse:
    user_prompt = (
        "Draft a single outreach email to the sponsor below about ONE selected event idea.\n\n"
        f"CLUB PROFILE JSON:\n{club.model_dump_json(by_alias=True)}\n\n"
        f"SPONSOR CONTEXT JSON:\n{sponsor.model_dump_json(by_alias=True)}\n\n"
        f"SELECTED EVENT IDEA JSON:\n{event_idea.model_dump_json(by_alias=True)}\n"
    )

    first_output = _call_llm(user_prompt)
    try:
        data: Any = json.loads(first_output)
        return EmailPitchResponse.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as first_error:
        fix_prompt = (
            "Your previous JSON was invalid. Return ONLY corrected JSON with keys subject and body.\n\n"
            f"ORIGINAL TASK:\n{user_prompt}\n\n"
            f"INVALID OUTPUT:\n{first_output}\n\n"
            f"ERROR:\n{first_error}\n"
        )
        second_output = _call_llm(fix_prompt)
        try:
            data2: Any = json.loads(second_output)
            return EmailPitchResponse.model_validate(data2)
        except (json.JSONDecodeError, ValidationError) as second_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"EmailAgent failed to return valid JSON: {second_error}",
            ) from second_error
