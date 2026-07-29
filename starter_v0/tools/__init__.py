from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .clarify.tool import ask_user
from .compare.tool import compare_items
from .fetch.tool import read_url
from .format.tool import render_digest
from .lookup.tool import web_search
from .newsletter.tool import compile_newsletter
from .papers.tool import arxiv_search
from .paper_text.tool import get_arxiv_paper_text
from .policy.tool import search_company_policy
from .send.tool import send_telegram
from .social_search.tool import search_tweets
from .summarize.tool import extract_key_points
from .timeline.tool import get_user_tweets
from .weather.tool import get_weather

TOOL_FUNCTIONS = {
    "clarify": ask_user,
    "timeline": get_user_tweets,
    "social_search": search_tweets,
    "lookup": web_search,
    "fetch": read_url,
    "format": render_digest,
    "summarize": extract_key_points,
    "newsletter": compile_newsletter,
    "compare": compare_items,
    "weather": get_weather,
    "send": send_telegram,
    "policy": search_company_policy,
    "papers": arxiv_search,
    "paper_text": get_arxiv_paper_text,
}


def load_tool_declarations(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tools"]


def to_openai_tools(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": item["name"],
            "description": item.get("description", ""),
            "parameters": item.get("parameters", {"type": "object", "properties": {}}),
        },
    } for item in declarations]
