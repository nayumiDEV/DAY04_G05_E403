from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 30


def err(tool: str, exc: Exception) -> dict[str, Any]:
    return {"tool": tool, "error": type(exc).__name__, "message": str(exc)}


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def fold_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def terms(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to",
        "ban", "bao", "can", "cho", "co", "cua", "duoc", "gi", "giup", "la", "lam", "minh", "mot", "nay",
        "nen", "the", "thi", "trong", "va", "ve", "voi",
    }
    folded = fold_text(text)
    return {term for term in re.findall(r"[a-z0-9]+", folded) if len(term) > 1 and term not in stopwords}


# ---- Shared Twitter helpers (deduplicated) ----

def twitter_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    key = os.getenv("RAPIDAPI_KEY")
    host = os.getenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
    if not key:
        raise RuntimeError("Missing RAPIDAPI_KEY env var")
    response = requests.get(
        f"https://{host}{path}",
        params=params,
        headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def tweet_item(raw: dict[str, Any]) -> dict[str, Any]:
    handle = raw.get("screen_name") or (raw.get("author") or {}).get("screen_name") or ""
    tweet_id = raw.get("tweet_id") or raw.get("id") or ""
    text = (raw.get("text") or "").strip()
    return {
        "title": text.split("\n")[0][:120],
        "summary": text,
        "url": f"https://x.com/{handle}/status/{tweet_id}" if handle and tweet_id else "",
        "source": f"@{handle}" if handle else "x.com",
        "date": raw.get("created_at"),
        "metrics": {"favorites": raw.get("favorites"), "retweets": raw.get("retweets"), "views": raw.get("views")},
    }


def tweets_from(data: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    raw_items = data.get("timeline") or data.get("tweets") or []
    items = [tweet_item(item) for item in raw_items if item.get("tweet_id") or item.get("id")]
    return items[: int(limit or 5)]

