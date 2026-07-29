from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


# WOEID (Where On Earth ID) — Yahoo's geo identifier used by Twitter trending API.
WOEID_BY_COUNTRY: dict[str, int] = {
    "worldwide": 1,
    "world": 1,
    "us": 23424977,
    "usa": 23424977,
    "united states": 23424977,
    "uk": 23424975,
    "united kingdom": 23424975,
    "vietnam": 23424984,
    "vn": 23424984,
    "japan": 23424856,
    "jp": 23424856,
    "germany": 23424829,
    "france": 23424819,
    "brazil": 23424768,
    "india": 23424848,
}


def _resolve_woeid(woeid: int | str, country: str = "") -> int:
    if woeid and int(woeid) > 1:
        return int(woeid)
    if country:
        key = country.strip().lower()
        return WOEID_BY_COUNTRY.get(key, 1)
    return 1


def get_trending_topics(woeid: int | str = 1, country: str = "", limit: int = 10) -> dict[str, Any]:
    """Fetch current trending topics on X/Twitter for a region.

    Uses the same Twitter API45 host as `timeline` (RapidAPI). Falls back to a
    small synthetic list if the upstream returns an error so the agent can still
    demonstrate the routing decision in offline / quota-exhausted demos.
    """
    try:
        woeid_resolved = _resolve_woeid(woeid, country)
        limit = max(1, min(int(limit or 10), 50))
        key = os.getenv("RAPIDAPI_KEY")
        items: list[dict[str, Any]] = []
        warning: str | None = None
        if key:
            try:
                response = requests.get(
                    "https://twitter-api45.p.rapidapi.com/trends.php",
                    params={"woeid": str(woeid_resolved)},
                    headers={
                        "x-rapidapi-key": key,
                        "x-rapidapi-host": "twitter-api45.p.rapidapi.com",
                    },
                    timeout=TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                raw = data.get("trends") if isinstance(data, dict) else None
                if isinstance(raw, list):
                    for entry in raw[:limit]:
                        name = entry.get("name") or entry.get("trend") or ""
                        if not name:
                            continue
                        items.append({
                            "name": name,
                            "query": entry.get("query") or name,
                            "tweet_volume": entry.get("tweet_volume"),
                            "url": entry.get("url") or f"https://twitter.com/search?q={name}",
                            "section": entry.get("trend_type") or "Trending",
                        })
            except Exception as exc:
                warning = f"Upstream trending API unavailable: {type(exc).__name__}: {exc}"
        if not items:
            # Offline fallback so the tool still returns a usable digest.
            fallback = [
                ("AI", 124000), ("#WorldCup", 88000), ("OpenAI", 71000),
                ("Climate", 56000), ("TechLayoffs", 41000), ("SpaceX", 33000),
                ("Crypto", 29000), ("GPT-5", 26000), ("Quantum", 19000),
                ("Robotics", 15000), ("#AIethics", 12000), ("Nvidia", 11000),
            ]
            items = [
                {
                    "name": name,
                    "query": name,
                    "tweet_volume": vol,
                    "url": f"https://twitter.com/search?q={name}",
                    "section": "Trending",
                }
                for name, vol in fallback[:limit]
            ]
            warning = warning or "Upstream trending API not configured; returning synthetic sample."
        return {
            "tool": "get_trending_topics",
            "woeid": woeid_resolved,
            "country": country or None,
            "limit": limit,
            "items": items,
            "warning": warning,
        }
    except Exception as exc:
        return err("get_trending_topics", exc)