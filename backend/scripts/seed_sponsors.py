"""
Seed sponsors into Postgres + generate embeddings.

Usage:
    cd backend
    python scripts/seed_sponsors.py

Idempotent: skips sponsors that already exist (by id).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import SponsorModel
from app.services.embedding_service import EmbeddingService
from app.data.sponsors_seed import SPONSORS


def sponsor_to_embed_text(s: dict) -> str:
    """Build the text we embed for a sponsor — same fields the matcher will compare against."""
    return (
        f"{s['name']}. {s['mission']} {s['description']} "
        f"Industries: {', '.join(s['industries'])}. "
        f"Support types: {', '.join(s['support_types'])}."
    )


def seed():
    db = SessionLocal()
    embedder = EmbeddingService()

    try:
        # Check which sponsors already exist
        existing_ids = {
            row[0]
            for row in db.execute(select(SponsorModel.id)).all()
        }

        new_sponsors = [s for s in SPONSORS if s["id"] not in existing_ids]

        if not new_sponsors:
            print(f"All {len(SPONSORS)} sponsors already seeded. Nothing to do.")
            return

        print(f"Seeding {len(new_sponsors)} new sponsors (skipping {len(existing_ids)} existing)...")

        for i, s in enumerate(new_sponsors, 1):
            print(f"  [{i}/{len(new_sponsors)}] {s['name']} — generating embedding...")

            embed_text = sponsor_to_embed_text(s)
            embedding = embedder.create_embedding(embed_text)

            sponsor = SponsorModel(
                id=s["id"],
                name=s["name"],
                mission=s["mission"],
                description=s.get("description"),
                industries=s["industries"],
                support_types=s["support_types"],
                budget_min_cents=s.get("budget_min_cents"),
                budget_max_cents=s.get("budget_max_cents"),
                contact_name=s.get("contact_name"),
                contact_email=s.get("contact_email"),
                website_url=s.get("website_url"),
                locations=s.get("locations"),
                embedding=embedding,
            )
            db.add(sponsor)

        db.commit()
        print(f"Seeded {len(new_sponsors)} sponsors with embeddings.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()