from __future__ import annotations

from datetime import datetime
from typing import Any

from tools._shared import domain


def compile_newsletter(items: list[dict[str, Any]] | None = None, title: str = "", date: str = "") -> dict[str, Any]:
    try:
        items = items or []
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        head = title or f"Research Newsletter — {date_str}"
        sections: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            sec = item.get("section") or item.get("source") or domain(item.get("url", "")) or "General"
            sections.setdefault(sec, []).append(item)
        parts = [f"# {head}", f"_{date_str}_ — {len(items)} items\n"]
        for sec, sec_items in sections.items():
            parts.append(f"## {sec}")
            for item in sec_items:
                t = item.get("title", "Untitled")
                s = (item.get("summary") or "")[:200]
                u = item.get("url", "")
                src = item.get("source") or domain(u) or ""
                link = f"[{src}]({u})" if u else src
                parts.append(f"- **{t}** — {s} ({link})")
            parts.append("")
        return {
            "tool": "compile_newsletter",
            "title": head,
            "date": date_str,
            "markdown": "\n".join(parts),
            "item_count": len(items),
        }
    except Exception as exc:
        return {"tool": "compile_newsletter", "error": type(exc).__name__, "message": str(exc)}
