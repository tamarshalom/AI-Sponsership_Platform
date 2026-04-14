from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ClubProfileModel(Base):
    __tablename__ = "clubs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    university: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    eboard_availability: Mapped[dict] = mapped_column(JSONB, nullable=False)
    preferred_industries: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    requested_support_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    member_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_goal_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SponsorModel(Base):
    __tablename__ = "sponsors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industries: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    support_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    budget_min_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    locations: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    sponsor_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EventSuggestionModel(Base):
    __tablename__ = "event_suggestions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    club_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sponsor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_attendees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    support_requested: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    sponsor_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    sponsor_match_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OutreachDraftModel(Base):
    __tablename__ = "outreach_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    club_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sponsor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_suggestion_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    personalization_tokens: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_send_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
