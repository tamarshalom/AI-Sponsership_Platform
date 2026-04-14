from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal  # noqa: E402
from app.schemas import SponsorIngestItem, SponsorIngestRequest  # noqa: E402
from app.services.sponsor_ingestion_service import SponsorIngestionService  # noqa: E402


def _split_multi(value: str | None) -> list[str]:
    if not value:
        return []
    chunks = [part.strip() for part in value.replace("|", ",").replace(";", ",").split(",")]
    return [chunk for chunk in chunks if chunk]


def _to_optional_int(value: str | None) -> int | None:
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def _row_to_item(row: dict[str, str]) -> SponsorIngestItem:
    metadata: dict[str, Any] = {}
    for key, value in row.items():
        if key.startswith("meta_") and value:
            metadata[key[5:]] = value

    return SponsorIngestItem(
        name=row.get("name", "").strip(),
        mission=row.get("mission", "").strip(),
        description=(row.get("description") or "").strip() or None,
        industries=_split_multi(row.get("industries")),
        supportTypes=_split_multi(row.get("support_types")),
        budgetMinCents=_to_optional_int(row.get("budget_min_cents")),
        budgetMaxCents=_to_optional_int(row.get("budget_max_cents")),
        contactName=(row.get("contact_name") or "").strip() or None,
        contactEmail=(row.get("contact_email") or "").strip() or None,
        websiteUrl=(row.get("website_url") or "").strip() or None,
        locations=_split_multi(row.get("locations")),
        externalId=(row.get("external_id") or "").strip() or None,
        metadata=metadata or None,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk ingest sponsors from CSV.")
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument(
        "--source",
        default="csv-upload",
        help="Source label written to sponsor metadata (default: csv-upload)",
    )
    parser.add_argument(
        "--reembed-existing",
        action="store_true",
        help="Recompute embeddings when rows match existing sponsors",
    )
    args = parser.parse_args()

    csv_file = Path(args.csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    with csv_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        print("No rows found in CSV.")
        return

    items = [_row_to_item(row) for row in rows]
    payload = SponsorIngestRequest(
        source=args.source,
        sponsors=items,
        reembedExisting=args.reembed_existing,
    )

    db = SessionLocal()
    try:
        service = SponsorIngestionService()
        result = service.ingest(db, payload)
        print(
            f"Ingest complete: processed={result.processed}, "
            f"created={result.created}, updated={result.updated}, "
            f"reembedded={result.reembedded}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
