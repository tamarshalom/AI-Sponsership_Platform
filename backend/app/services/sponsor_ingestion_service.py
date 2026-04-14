"""Sponsor ingestion, deduplication, and embedding refresh."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SponsorModel
from app.schemas import (
    SponsorIngestItem,
    SponsorIngestRequest,
    SponsorIngestResponse,
    SponsorReembedResponse,
)
from app.services.embedding_service import EmbeddingService


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _normalize_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "unknown"


def _extract_domain(website_url: str | None) -> str | None:
    if not website_url:
        return None
    candidate = website_url.strip()
    if not candidate:
        return None
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = parsed.netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _dedupe_key(item: SponsorIngestItem) -> str:
    domain = _extract_domain(item.website_url)
    if domain:
        return domain
    return _normalize_text(item.name).lower()


def _build_sponsor_id(source: str, dedupe_key: str) -> str:
    source_slug = _normalize_slug(source)[:24]
    key_slug = _normalize_slug(dedupe_key)[:24]
    digest = hashlib.sha1(f"{source}:{dedupe_key}".encode("utf-8")).hexdigest()[:10]
    return f"sponsor-{source_slug}-{key_slug}-{digest}"


def _normalize_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in values:
        clean = _normalize_text(raw)
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(clean)
    return normalized


def _embedding_text(item: SponsorIngestItem) -> str:
    website = item.website_url or ""
    description = item.description or ""
    return (
        f"Name: {item.name}\n"
        f"Mission: {item.mission}\n"
        f"Description: {description}\n"
        f"Industries: {', '.join(item.industries)}\n"
        f"Support Types: {', '.join(item.support_types)}\n"
        f"Locations: {', '.join(item.locations)}\n"
        f"Website: {website}\n"
    )


@dataclass
class _IngestCounters:
    processed: int = 0
    created: int = 0
    updated: int = 0
    reembedded: int = 0


class SponsorIngestionService:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embeddings = embedding_service or EmbeddingService()

    def ingest(self, db: Session, payload: SponsorIngestRequest) -> SponsorIngestResponse:
        counters = _IngestCounters()
        sponsor_ids: list[str] = []

        for item in payload.sponsors:
            counters.processed += 1
            normalized_item = self._normalize_item(item)
            dedupe_key = _dedupe_key(normalized_item)
            existing = self._find_existing(db, normalized_item)
            should_reembed = existing is None or payload.reembed_existing

            if existing is None:
                sponsor = SponsorModel(
                    id=_build_sponsor_id(payload.source, dedupe_key),
                    name=normalized_item.name,
                    mission=normalized_item.mission,
                    description=normalized_item.description,
                    industries=normalized_item.industries,
                    support_types=normalized_item.support_types,
                    budget_min_cents=normalized_item.budget_min_cents,
                    budget_max_cents=normalized_item.budget_max_cents,
                    contact_name=normalized_item.contact_name,
                    contact_email=normalized_item.contact_email,
                    website_url=normalized_item.website_url,
                    locations=normalized_item.locations,
                    sponsor_metadata=self._build_metadata(payload.source, normalized_item, None),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(sponsor)
                counters.created += 1
            else:
                sponsor = existing
                sponsor.name = normalized_item.name
                sponsor.mission = normalized_item.mission
                sponsor.description = normalized_item.description
                sponsor.industries = normalized_item.industries
                sponsor.support_types = normalized_item.support_types
                sponsor.budget_min_cents = normalized_item.budget_min_cents
                sponsor.budget_max_cents = normalized_item.budget_max_cents
                sponsor.contact_name = normalized_item.contact_name
                sponsor.contact_email = normalized_item.contact_email
                sponsor.website_url = normalized_item.website_url
                sponsor.locations = normalized_item.locations
                sponsor.sponsor_metadata = self._build_metadata(
                    payload.source,
                    normalized_item,
                    sponsor.sponsor_metadata,
                )
                sponsor.updated_at = datetime.now(timezone.utc)
                counters.updated += 1

            if should_reembed:
                sponsor.embedding = self._embeddings.create_embedding(
                    _embedding_text(normalized_item)
                )
                counters.reembedded += 1

            sponsor_ids.append(sponsor.id)

        db.commit()
        return SponsorIngestResponse(
            source=payload.source,
            processed=counters.processed,
            created=counters.created,
            updated=counters.updated,
            reembedded=counters.reembedded,
            sponsor_ids=sponsor_ids,
        )

    def reembed_all(self, db: Session) -> SponsorReembedResponse:
        sponsors = db.execute(select(SponsorModel)).scalars().all()
        reembedded = 0
        for sponsor in sponsors:
            item = SponsorIngestItem(
                name=sponsor.name,
                mission=sponsor.mission,
                description=sponsor.description,
                industries=sponsor.industries or [],
                support_types=sponsor.support_types or [],
                budget_min_cents=sponsor.budget_min_cents,
                budget_max_cents=sponsor.budget_max_cents,
                contact_name=sponsor.contact_name,
                contact_email=sponsor.contact_email,
                website_url=sponsor.website_url,
                locations=sponsor.locations or [],
                metadata=sponsor.sponsor_metadata,
            )
            sponsor.embedding = self._embeddings.create_embedding(_embedding_text(item))
            sponsor.updated_at = datetime.now(timezone.utc)
            reembedded += 1
        db.commit()
        return SponsorReembedResponse(total_sponsors=len(sponsors), reembedded=reembedded)

    def _find_existing(self, db: Session, item: SponsorIngestItem) -> SponsorModel | None:
        domain = _extract_domain(item.website_url)
        if domain:
            matches = db.execute(
                select(SponsorModel).where(SponsorModel.website_url.is_not(None))
            ).scalars()
            for candidate in matches:
                if _extract_domain(candidate.website_url) == domain:
                    return candidate

        return db.execute(
            select(SponsorModel).where(
                func.lower(SponsorModel.name) == item.name.strip().lower()
            )
        ).scalar_one_or_none()

    @staticmethod
    def _build_metadata(
        source: str,
        item: SponsorIngestItem,
        existing: dict | None,
    ) -> dict:
        metadata = dict(existing or {})
        metadata["source"] = source
        metadata["lastIngestedAt"] = datetime.now(timezone.utc).isoformat()
        if item.external_id:
            metadata["sourceExternalId"] = item.external_id
        if item.metadata:
            metadata.update(item.metadata)
        return metadata

    @staticmethod
    def _normalize_item(item: SponsorIngestItem) -> SponsorIngestItem:
        return SponsorIngestItem(
            name=_normalize_text(item.name),
            mission=_normalize_text(item.mission),
            description=_normalize_text(item.description) if item.description else None,
            industries=_normalize_list(item.industries),
            support_types=_normalize_list(item.support_types),
            budget_min_cents=item.budget_min_cents,
            budget_max_cents=item.budget_max_cents,
            contact_name=_normalize_text(item.contact_name) if item.contact_name else None,
            contact_email=_normalize_text(item.contact_email) if item.contact_email else None,
            website_url=_normalize_text(item.website_url) if item.website_url else None,
            locations=_normalize_list(item.locations),
            metadata=item.metadata,
            external_id=item.external_id,
        )
