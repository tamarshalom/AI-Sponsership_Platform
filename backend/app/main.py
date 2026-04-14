from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import SessionLocal
from app.models import ClubProfileModel
from app.email_agent import generate_sponsorship_pitch
from app.event_strategy_agent import generate_event_strategies
from app.profile_agent import parse_club_profile_from_raw_text
from app.schemas import (
    ClubProfile,
    EmailAgentRequest,
    EmailPitchResponse,
    EventStrategyAgentRequest,
    EventStrategyAgentResponse,
    MatchSponsorsResponse,
    ProfileAgentRequest,
    Sponsor,
    SponsorIngestRequest,
    SponsorIngestResponse,
    SponsorReembedResponse,
)
from app.services.sponsor_match_service import SponsorMatchService
from app.services.sponsor_ingestion_service import SponsorIngestionService
from app.services.web_sponsor_discovery_service import WebSponsorDiscoveryService
from app.models import SponsorModel

app = FastAPI(title=settings.app_name)

_cors_origins = [
    o.strip()
    for o in settings.frontend_origins.split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> RedirectResponse:
    """Avoid a bare 404 when opening the API root in a browser."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/clubs", response_model=ClubProfile, status_code=status.HTTP_201_CREATED)
def create_club(payload: ClubProfile, db: Session = Depends(get_db)) -> ClubProfile:
    club = ClubProfileModel(
        id=payload.id,
        name=payload.name,
        mission=payload.mission,
        description=payload.description,
        university=payload.university,
        website_url=payload.website_url,
        social_links=payload.social_links,
        contact_email=payload.contact_email,
        eboard_availability=payload.eboard_availability,
        preferred_industries=payload.preferred_industries,
        requested_support_types=payload.requested_support_types,
        member_count=payload.member_count,
        budget_goal_cents=payload.budget_goal_cents,
        created_at=payload.created_at,
        updated_at=payload.updated_at,
    )
    db.add(club)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Club with this ID already exists.",
        ) from exc
    db.refresh(club)
    return ClubProfile.model_validate(club)


@app.get("/clubs/{club_id}", response_model=ClubProfile)
def get_club(club_id: str, db: Session = Depends(get_db)) -> ClubProfile:
    club = db.get(ClubProfileModel, club_id)
    if club is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Club not found."
        )
    return ClubProfile.model_validate(club)


@app.post("/agents/profile/parse", response_model=ClubProfile)
def parse_profile(payload: ProfileAgentRequest) -> ClubProfile:
    return parse_club_profile_from_raw_text(payload.raw_text)


_match_service = SponsorMatchService()
_ingestion_service = SponsorIngestionService()
_web_discovery_service = WebSponsorDiscoveryService(_ingestion_service)


@app.post("/match-sponsors", response_model=MatchSponsorsResponse)
def match_sponsors(payload: ClubProfile, db: Session = Depends(get_db)) -> MatchSponsorsResponse:
    result = _match_service.match_top_sponsors(db, payload, limit=5)
    top_score = max((m.score for m in result.matches), default=0.0)

    should_discover = (
        settings.match_web_discovery_enabled
        and top_score < settings.match_web_discovery_trigger_score
    )
    if should_discover:
        try:
            discovered = _web_discovery_service.discover_and_ingest(
                db,
                payload,
                max_new=settings.match_web_discovery_max_new,
            )
            if discovered > 0:
                result = _match_service.match_top_sponsors(db, payload, limit=5)
        except Exception:
            # Never fail sponsor matching due to optional discovery.
            pass
    return result


@app.get("/sponsors", response_model=list[Sponsor])
def list_sponsors(db: Session = Depends(get_db), limit: int = 100) -> list[Sponsor]:
    sponsors = db.query(SponsorModel).order_by(SponsorModel.updated_at.desc()).limit(limit).all()
    return [Sponsor.model_validate(s) for s in sponsors]


@app.post("/admin/sponsors/ingest", response_model=SponsorIngestResponse)
def ingest_sponsors(
    payload: SponsorIngestRequest, db: Session = Depends(get_db)
) -> SponsorIngestResponse:
    return _ingestion_service.ingest(db, payload)


@app.post("/admin/sponsors/reembed", response_model=SponsorReembedResponse)
def reembed_sponsors(db: Session = Depends(get_db)) -> SponsorReembedResponse:
    return _ingestion_service.reembed_all(db)


@app.post("/agents/event-strategy", response_model=EventStrategyAgentResponse)
def event_strategy_agent(payload: EventStrategyAgentRequest) -> EventStrategyAgentResponse:
    return generate_event_strategies(payload.club, payload.sponsor)


@app.post("/agents/email-pitch", response_model=EmailPitchResponse)
def email_agent(payload: EmailAgentRequest) -> EmailPitchResponse:
    return generate_sponsorship_pitch(
        payload.club, payload.sponsor, payload.event_idea
    )
