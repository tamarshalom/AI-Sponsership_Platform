"""Initial tables and pgvector extension.

Revision ID: 20260407_0001
Revises:
Create Date: 2026-04-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260407_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "clubs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mission", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("university", sa.String(length=255), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("social_links", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column(
            "eboard_availability",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "preferred_industries",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "requested_support_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("member_count", sa.Integer(), nullable=True),
        sa.Column("budget_goal_cents", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "sponsors",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mission", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industries", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("support_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("budget_min_cents", sa.Integer(), nullable=True),
        sa.Column("budget_max_cents", sa.Integer(), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("locations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "event_suggestions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("club_id", sa.String(length=64), nullable=False),
        sa.Column("sponsor_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("proposed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_attendees", sa.Integer(), nullable=True),
        sa.Column("support_requested", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sponsor_match_score", sa.Float(), nullable=False),
        sa.Column(
            "sponsor_match_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_event_suggestions_club_id", "event_suggestions", ["club_id"])
    op.create_index("ix_event_suggestions_sponsor_id", "event_suggestions", ["sponsor_id"])

    op.create_table(
        "outreach_drafts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("club_id", sa.String(length=64), nullable=False),
        sa.Column("sponsor_id", sa.String(length=64), nullable=False),
        sa.Column("event_suggestion_id", sa.String(length=64), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "personalization_tokens",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("scheduled_send_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_outreach_drafts_club_id", "outreach_drafts", ["club_id"])
    op.create_index("ix_outreach_drafts_sponsor_id", "outreach_drafts", ["sponsor_id"])

def downgrade() -> None:
    op.drop_index("ix_outreach_drafts_sponsor_id", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_club_id", table_name="outreach_drafts")
    op.drop_table("outreach_drafts")
    op.drop_index("ix_event_suggestions_sponsor_id", table_name="event_suggestions")
    op.drop_index("ix_event_suggestions_club_id", table_name="event_suggestions")
    op.drop_table("event_suggestions")
    op.drop_table("sponsors")
    op.drop_table("clubs")
