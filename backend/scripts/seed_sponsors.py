from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal  # noqa: E402
from app.services.embedding_service import EmbeddingService  # noqa: E402
from app.models import SponsorModel  # noqa: E402


MOCK_SPONSORS = [
    {
        "id": "sponsor-red-bull",
        "name": "Red Bull",
        "mission": "Fuel ambitious student communities through high-energy experiences.",
        "description": "Supports campus events, esports tournaments, and late-night hackathon activations.",
        "industries": ["beverage", "consumer brand", "sports"],
        "support_types": ["product", "cash", "event activation"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-google-cloud",
        "name": "Google Cloud",
        "mission": "Empower builders with modern cloud and AI tools.",
        "description": "Sponsors technical workshops, cloud credits, and startup-oriented events.",
        "industries": ["cloud", "ai", "developer tools"],
        "support_types": ["credits", "speakers", "cash"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-microsoft-azure",
        "name": "Microsoft Azure",
        "mission": "Enable student innovation with secure and scalable infrastructure.",
        "description": "Funds student developer clubs and provides mentors for cloud architecture sessions.",
        "industries": ["cloud", "enterprise software"],
        "support_types": ["credits", "mentorship", "cash"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-amazon-aws",
        "name": "Amazon Web Services",
        "mission": "Accelerate learning through practical cloud experiences.",
        "description": "Supports hackathons and bootcamps with judges, grants, and cloud resources.",
        "industries": ["cloud", "platform"],
        "support_types": ["credits", "judges", "cash"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-openai",
        "name": "OpenAI",
        "mission": "Advance AI literacy and responsible deployment.",
        "description": "Sponsors AI clubs, model prototyping nights, and ethics panels.",
        "industries": ["artificial intelligence", "research"],
        "support_types": ["api credits", "speakers", "cash"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-notion",
        "name": "Notion",
        "mission": "Help teams organize knowledge and collaborate effectively.",
        "description": "Supports productivity-focused clubs with workspace credits and workshops.",
        "industries": ["productivity software", "saas"],
        "support_types": ["software", "swag", "cash"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-figma",
        "name": "Figma",
        "mission": "Make design more collaborative and accessible.",
        "description": "Partners with design and product clubs for UI/UX competitions and portfolio reviews.",
        "industries": ["design", "saas"],
        "support_types": ["licenses", "judges", "swag"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-github",
        "name": "GitHub",
        "mission": "Support developer communities building in the open.",
        "description": "Sponsorship for coding clubs, open-source events, and maintainer meetups.",
        "industries": ["developer tools", "software engineering"],
        "support_types": ["software", "speakers", "cash"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-datadog",
        "name": "Datadog",
        "mission": "Help teams build reliable systems through observability.",
        "description": "Sponsors backend and systems clubs, reliability workshops, and monitoring challenges.",
        "industries": ["devops", "observability"],
        "support_types": ["credits", "speakers", "cash"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-snowflake",
        "name": "Snowflake",
        "mission": "Make data collaboration and analytics easier for all teams.",
        "description": "Supports data science organizations with platform credits and mentors.",
        "industries": ["data", "analytics"],
        "support_types": ["credits", "mentorship", "cash"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-capital-one",
        "name": "Capital One",
        "mission": "Grow the next generation of technologists and leaders.",
        "description": "Funds fintech and coding events, case competitions, and women-in-tech programs.",
        "industries": ["finance", "fintech"],
        "support_types": ["cash", "speakers", "career opportunities"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-jpmorgan",
        "name": "JPMorgan Chase",
        "mission": "Invest in talent pipelines and inclusive innovation.",
        "description": "Supports finance and consulting clubs with networking events and sponsorship grants.",
        "industries": ["banking", "finance"],
        "support_types": ["cash", "mentorship", "event speakers"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-rei",
        "name": "REI Co-op",
        "mission": "Promote outdoor stewardship and active lifestyles.",
        "description": "Sponsors environmental and outdoor clubs for trail cleanups and adventure outings.",
        "industries": ["retail", "outdoors"],
        "support_types": ["gear", "gift cards", "cash"],
        "locations": ["regional"],
    },
    {
        "id": "sponsor-patagonia",
        "name": "Patagonia",
        "mission": "Support climate action and environmental justice initiatives.",
        "description": "Funds sustainability-focused student organizations and awareness campaigns.",
        "industries": ["apparel", "sustainability"],
        "support_types": ["cash", "grants", "product"],
        "locations": ["national"],
    },
    {
        "id": "sponsor-roasters-district",
        "name": "Roasters District Coffee",
        "mission": "Energize local student communities through quality coffee and community events.",
        "description": "Local coffee chain sponsoring finals-week popups, club mixers, and study nights.",
        "industries": ["food and beverage", "local business"],
        "support_types": ["in-kind", "gift cards", "cash"],
        "locations": ["local"],
    },
    {
        "id": "sponsor-luma-cafe",
        "name": "Luma Cafe",
        "mission": "Create welcoming spaces for students to connect and create.",
        "description": "Neighborhood cafe sponsoring open mics, art nights, and club fundraising events.",
        "industries": ["food and beverage", "community"],
        "support_types": ["in-kind", "venue", "gift cards"],
        "locations": ["local"],
    },
    {
        "id": "sponsor-nvidia",
        "name": "NVIDIA",
        "mission": "Power the future of AI, graphics, and accelerated computing.",
        "description": "Supports AI research groups, robotics teams, and GPU-heavy hackathons.",
        "industries": ["hardware", "ai"],
        "support_types": ["hardware grants", "speakers", "cash"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-spotify",
        "name": "Spotify",
        "mission": "Unlock creativity by connecting artists, listeners, and builders.",
        "description": "Sponsors music-tech clubs, podcast labs, and creator economy events.",
        "industries": ["music", "media", "technology"],
        "support_types": ["cash", "mentors", "promotion"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-stripe",
        "name": "Stripe",
        "mission": "Increase the GDP of the internet through better financial infrastructure.",
        "description": "Supports entrepreneurship clubs with fintech talks and startup challenge prizes.",
        "industries": ["payments", "fintech"],
        "support_types": ["cash", "credits", "mentorship"],
        "locations": ["global"],
    },
    {
        "id": "sponsor-tech-repair-hub",
        "name": "Tech Repair Hub",
        "mission": "Make technology more accessible and sustainable in the local community.",
        "description": "Local computer repair business sponsoring robotics teams and maker spaces.",
        "industries": ["local business", "hardware services"],
        "support_types": ["in-kind", "tools", "cash"],
        "locations": ["local"],
    },
]


def build_embedding_text(sponsor: dict) -> str:
    return (
        f"Name: {sponsor['name']}\n"
        f"Mission: {sponsor['mission']}\n"
        f"Description: {sponsor['description']}\n"
        f"Industries: {', '.join(sponsor['industries'])}\n"
        f"Support Types: {', '.join(sponsor['support_types'])}\n"
        f"Locations: {', '.join(sponsor['locations'])}\n"
    )


def main() -> None:
    session = SessionLocal()
    embeddings = EmbeddingService()
    now = datetime.now(timezone.utc)
    created = 0
    updated = 0

    try:
        for sponsor in MOCK_SPONSORS:
            embedding = embeddings.create_embedding(build_embedding_text(sponsor))

            existing = session.scalar(
                select(SponsorModel).where(SponsorModel.id == sponsor["id"])
            )
            if existing is None:
                row = SponsorModel(
                    id=sponsor["id"],
                    name=sponsor["name"],
                    mission=sponsor["mission"],
                    description=sponsor["description"],
                    industries=sponsor["industries"],
                    support_types=sponsor["support_types"],
                    budget_min_cents=50000,
                    budget_max_cents=2500000,
                    contact_name="Sponsorship Team",
                    contact_email=f"partners@{sponsor['id'].replace('sponsor-', '').replace('-', '')}.com",
                    website_url=None,
                    locations=sponsor["locations"],
                    sponsor_metadata={"seeded": True},
                    embedding=embedding,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                created += 1
            else:
                existing.name = sponsor["name"]
                existing.mission = sponsor["mission"]
                existing.description = sponsor["description"]
                existing.industries = sponsor["industries"]
                existing.support_types = sponsor["support_types"]
                existing.locations = sponsor["locations"]
                existing.embedding = embedding
                existing.updated_at = now
                updated += 1

        session.commit()
        print(f"Seed complete. created={created}, updated={updated}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
