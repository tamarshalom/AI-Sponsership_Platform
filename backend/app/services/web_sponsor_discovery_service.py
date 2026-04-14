"""Discover potential sponsors from web search and ingest them."""

from __future__ import annotations

import json
import logging
import re
from urllib.parse import unquote, urlparse

import httpx
from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import ClubProfile, SponsorIngestItem, SponsorIngestRequest
from app.services.sponsor_ingestion_service import SponsorIngestionService

logger = logging.getLogger(__name__)


def _club_query_terms(club: ClubProfile) -> list[str]:
    base = [club.mission]
    if club.description:
        base.append(club.description)
    base.extend(club.preferred_industries or [])
    base.extend(club.requested_support_types or [])
    text = " ".join(base).lower()
    words = re.findall(r"[a-z]{4,}", text)
    stop = {
        "club",
        "students",
        "student",
        "through",
        "events",
        "event",
        "community",
        "support",
        "sponsorship",
        "sponsor",
        "raise",
        "awareness",
    }
    unique: list[str] = []
    seen: set[str] = set()
    for word in words:
        if word in stop or word in seen:
            continue
        seen.add(word)
        unique.append(word)
        if len(unique) >= 6:
            break
    return unique


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _search_duckduckgo(query: str, max_results: int = 12) -> list[dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
    }
    with httpx.Client(timeout=12.0, headers=headers, follow_redirects=True) as client:
        response = client.get("https://lite.duckduckgo.com/lite/", params={"q": query})
        response.raise_for_status()
    html = response.text

    anchors = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.IGNORECASE | re.DOTALL)
    snippets = re.findall(r"<td class='result-snippet'>(.*?)</td>", html, flags=re.IGNORECASE | re.DOTALL)

    cleaned_snippets: list[str] = []
    for a, b in snippets:
        raw = a or b
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        if raw:
            cleaned_snippets.append(unquote(raw))

    results: list[dict] = []
    for i, (href, title_html) in enumerate(anchors):
        if len(results) >= max_results:
            break
        title = re.sub(r"<[^>]+>", " ", title_html)
        title = re.sub(r"\s+", " ", title).strip()
        url = unquote(href)
        if "duckduckgo.com" in url and "uddg=" in url:
            m = re.search(r"uddg=([^&]+)", url)
            if m:
                url = unquote(m.group(1))
        if not url.startswith("http"):
            continue
        domain = _extract_domain(url)
        if not domain:
            continue
        snippet = cleaned_snippets[i] if i < len(cleaned_snippets) else ""
        results.append({"title": title, "url": url, "domain": domain, "snippet": snippet})
    return results


def _extract_sponsors_with_llm(club: ClubProfile, web_results: list[dict], max_new: int) -> list[SponsorIngestItem]:
    if not settings.openai_api_key or not web_results:
        return []

    client = OpenAI(api_key=settings.openai_api_key)
    payload = json.dumps(web_results[:18], ensure_ascii=False)
    prompt = (
        "You are extracting potential sponsorship organizations from web search results.\n"
        "Given club context and search snippets, return only likely organizations/brands "
        "that could sponsor the club.\n\n"
        f"CLUB MISSION:\n{club.mission}\n\n"
        f"CLUB DESCRIPTION:\n{club.description or ''}\n\n"
        f"PREFERRED INDUSTRIES: {', '.join(club.preferred_industries or [])}\n"
        f"REQUESTED SUPPORT TYPES: {', '.join(club.requested_support_types or [])}\n\n"
        "WEB RESULTS JSON:\n"
        f"{payload}\n\n"
        "Return JSON format:\n"
        "{ \"sponsors\": [ {\"name\":\"...\", \"mission\":\"...\", \"description\":\"...\", "
        "\"industries\":[\"...\"], \"supportTypes\":[\"...\"], \"websiteUrl\":\"https://...\", "
        "\"locations\":[\"...\"], \"externalId\":\"optional\"} ] }\n"
        f"Return at most {max_new} sponsors. Only include orgs that plausibly match this club."
    )
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Web discovery LLM extraction failed: %s", exc)
        return []

    items: list[SponsorIngestItem] = []
    for row in data.get("sponsors", [])[:max_new]:
        if not isinstance(row, dict):
            continue
        try:
            item = SponsorIngestItem.model_validate(row)
            if item.website_url and item.name and item.mission:
                items.append(item)
        except Exception:
            continue
    return items


def _heuristic_sponsors(club: ClubProfile, web_results: list[dict], max_new: int) -> list[SponsorIngestItem]:
    items: list[SponsorIngestItem] = []
    seen_domains: set[str] = set()
    for row in web_results:
        if len(items) >= max_new:
            break
        domain = str(row.get("domain") or "").strip().lower()
        title = str(row.get("title") or "").strip()
        snippet = str(row.get("snippet") or "").strip()
        url = str(row.get("url") or "").strip()
        if not domain or not url or domain in seen_domains:
            continue
        if any(bad in domain for bad in {"wikipedia.org", "reddit.com", "youtube.com"}):
            continue

        name = re.split(r"\s[-|]\s", title)[0].strip() if title else domain.split(".")[0].title()
        mission = snippet or (
            f"Potential sponsor discovered for {club.name} based on {club.mission[:120]}."
        )
        try:
            item = SponsorIngestItem(
                name=name,
                mission=mission,
                description=snippet or None,
                industries=club.preferred_industries[:3],
                supportTypes=club.requested_support_types[:3],
                websiteUrl=url,
                locations=["unknown"],
                metadata={"discoveryMethod": "heuristic"},
            )
        except Exception:
            continue
        items.append(item)
        seen_domains.add(domain)
    return items


class WebSponsorDiscoveryService:
    def __init__(self, ingestion_service: SponsorIngestionService | None = None) -> None:
        self._ingestion = ingestion_service or SponsorIngestionService()

    def discover_and_ingest(self, db: Session, club: ClubProfile, max_new: int) -> int:
        terms = _club_query_terms(club)
        if not terms:
            return 0
        query = (
            f"{club.university} student club sponsorship "
            f"{' '.join(terms)} organizations companies"
        )
        try:
            results = _search_duckduckgo(query, max_results=16)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DuckDuckGo search failed: %s", exc)
            return 0

        items = _extract_sponsors_with_llm(club, results, max_new=max_new)
        if not items:
            items = _heuristic_sponsors(club, results, max_new=max_new)
        if not items:
            return 0

        ingest = SponsorIngestRequest(
            source="web-discovery",
            sponsors=items,
            reembedExisting=False,
        )
        response = self._ingestion.ingest(db, ingest)
        return response.created + response.updated
