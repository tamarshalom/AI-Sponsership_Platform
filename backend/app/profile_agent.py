from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import ValidationError

from app.config import settings
from app.schemas import ClubProfile


SYSTEM_PROMPT = """You are a data extraction assistant for a sponsorship platform.
Return ONLY valid JSON and no prose.
Generate a ClubProfile object that strictly follows this schema:
- id: string
- name: string
- mission: string
- description: string | null
- university: string
- websiteUrl: string | null
- socialLinks: object<string, string> | null
- contactEmail: string
- eboardAvailability: object<string, any>
- preferredIndustries: string[]
- requestedSupportTypes: string[]
- memberCount: number | null
- budgetGoalCents: number | null
- createdAt: ISO datetime string
- updatedAt: ISO datetime string

If fields are missing in source text, infer sensible placeholders.
For unknown emails, use "unknown@example.com".
Ensure createdAt/updatedAt are valid ISO 8601 datetimes.
"""


def _call_llm(prompt: str) -> str:
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
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Model returned empty content.")
    return content


def parse_club_profile_from_raw_text(raw_text: str) -> ClubProfile:
    base_prompt = (
        "Extract a ClubProfile from this club text.\n\n"
        f"RAW CLUB TEXT:\n{raw_text}\n"
    )

    first_output = _call_llm(base_prompt)
    try:
        first_json: Any = json.loads(first_output)
        return ClubProfile.model_validate(first_json)
    except (json.JSONDecodeError, ValidationError) as first_error:
        fix_prompt = (
            "Your previous output was invalid JSON for ClubProfile.\n"
            "Fix it and return ONLY corrected JSON.\n\n"
            f"RAW CLUB TEXT:\n{raw_text}\n\n"
            f"INVALID OUTPUT:\n{first_output}\n\n"
            f"ERROR:\n{str(first_error)}\n"
        )
        second_output = _call_llm(fix_prompt)
        try:
            second_json: Any = json.loads(second_output)
            return ClubProfile.model_validate(second_json)
        except (json.JSONDecodeError, ValidationError) as second_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Profile Agent failed to return valid ClubProfile JSON: {second_error}",
            ) from second_error
