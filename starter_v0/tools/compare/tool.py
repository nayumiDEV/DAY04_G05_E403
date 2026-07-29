from __future__ import annotations

from typing import Any

from tools._shared import domain


def compare_items(items: list[dict[str, Any]] | None = None, aspect: str = "overview") -> dict[str, Any]:
    try:
        items = items or []
        if len(items) < 2:
            return {
                "tool": "compare_items",
                "error": "need at least 2 items to compare",
                "item_count": len(items),
            }
        rows = []
        for i, item in enumerate(items, 1):
            t = item.get("title", "Untitled")
            s = (item.get("summary") or "")[:300]
            u = item.get("url", "")
            src = item.get("source") or domain(u) or "Unknown"
            rows.append(f"### Item {i}: {t}")
            rows.append(f"- **Source**: {src}")
            rows.append(f"- **URL**: {u}" if u else "")
            rows.append(f"- **Summary**: {s}")
            rows.append("")

        if aspect == "differences":
            focus = "### Key Differences\n\n(Topics, claims, or angles that differ between the items — review the summaries above.)"
        elif aspect == "similarities":
            focus = "### Common Themes\n\n(Overlapping topics, shared findings, or similar conclusions — review the summaries above.)"
        else:
            focus = "### Comparison Notes\n\n(Review each item's details above and consider differences in sources, timeframes, and coverage.)"

        return {
            "tool": "compare_items",
            "aspect": aspect,
            "item_count": len(items),
            "markdown": "\n".join(rows) + "\n" + focus,
        }
    except Exception as exc:
        return {"tool": "compare_items", "error": type(exc).__name__, "message": str(exc)}
