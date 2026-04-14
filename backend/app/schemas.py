from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AppSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        ser_json_by_alias=True,
    )


class ClubProfile(AppSchema):
    id: str
    name: str
    mission: str
    description: Optional[str] = None
    university: str
    website_url: Optional[str] = Field(default=None, alias="websiteUrl")
    social_links: Optional[Dict[str, str]] = Field(default=None, alias="socialLinks")
    contact_email: str = Field(alias="contactEmail")
    eboard_availability: Dict[str, Any] = Field(alias="eboardAvailability")
    preferred_industries: List[str] = Field(alias="preferredIndustries")
    requested_support_types: List[str] = Field(alias="requestedSupportTypes")
    member_count: Optional[int] = Field(default=None, alias="memberCount")
    budget_goal_cents: Optional[int] = Field(default=None, alias="budgetGoalCents")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class Sponsor(AppSchema):
    id: str
    name: str
    mission: str
    description: Optional[str] = None
    industries: List[str]
    support_types: List[str] = Field(alias="supportTypes")
    budget_min_cents: Optional[int] = Field(default=None, alias="budgetMinCents")
    budget_max_cents: Optional[int] = Field(default=None, alias="budgetMaxCents")
    contact_name: Optional[str] = Field(default=None, alias="contactName")
    contact_email: Optional[str] = Field(default=None, alias="contactEmail")
    website_url: Optional[str] = Field(default=None, alias="websiteUrl")
    locations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class EventSuggestion(AppSchema):
    id: str
    club_id: str = Field(alias="clubId")
    sponsor_id: str = Field(alias="sponsorId")
    title: str
    summary: str
    rationale: str
    proposed_date: Optional[datetime] = Field(default=None, alias="proposedDate")
    estimated_attendees: Optional[int] = Field(default=None, alias="estimatedAttendees")
    support_requested: List[str] = Field(alias="supportRequested")
    sponsor_match_score: float = Field(alias="sponsorMatchScore")
    sponsor_match_breakdown: Dict[str, float] = Field(alias="sponsorMatchBreakdown")
    tags: Optional[List[str]] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class OutreachDraft(AppSchema):
    id: str
    club_id: str = Field(alias="clubId")
    sponsor_id: str = Field(alias="sponsorId")
    event_suggestion_id: Optional[str] = Field(default=None, alias="eventSuggestionId")
    subject: str
    body: str
    personalization_tokens: Optional[Dict[str, str]] = Field(
        default=None, alias="personalizationTokens"
    )
    status: Literal["draft", "ready", "sent"]
    reviewer_notes: Optional[str] = Field(default=None, alias="reviewerNotes")
    scheduled_send_at: Optional[datetime] = Field(default=None, alias="scheduledSendAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ProfileAgentRequest(AppSchema):
    raw_text: str = Field(min_length=10, alias="rawText")


class MatchSponsorsResult(AppSchema):
    sponsor_id: str = Field(alias="sponsorId")
    sponsor_name: str = Field(alias="sponsorName")
    mission: str
    description: Optional[str] = None
    score: float
    reasons: Optional[List[str]] = None
    suggested_activation: Optional[str] = Field(default=None, alias="suggestedActivation")


class MatchSponsorsResponse(AppSchema):
    matches: List[MatchSponsorsResult]


class SponsorBrief(AppSchema):
    """Minimal sponsor context for agents (e.g. from match results or full Sponsor)."""

    id: str
    name: str
    mission: str
    description: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    support_types: List[str] = Field(default_factory=list, alias="supportTypes")


class EventStrategyIdea(AppSchema):
    """One proposed event (agent output; not persisted until saved as EventSuggestion)."""

    title: str
    summary: str
    rationale: str
    estimated_attendees: Optional[int] = Field(default=None, alias="estimatedAttendees")
    support_requested: List[str] = Field(alias="supportRequested")
    tags: Optional[List[str]] = None


class EventStrategyAgentResponse(AppSchema):
    ideas: List[EventStrategyIdea] = Field(min_length=3, max_length=3)


class EventStrategyAgentRequest(AppSchema):
    club: ClubProfile
    sponsor: SponsorBrief


class EmailPitchResponse(AppSchema):
    subject: str
    body: str


class EmailAgentRequest(AppSchema):
    club: ClubProfile
    sponsor: SponsorBrief
    event_idea: EventStrategyIdea = Field(alias="eventIdea")
