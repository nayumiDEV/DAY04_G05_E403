from __future__ import annotations

import re
from typing import Any


def extract_key_points(text: str = "", max_points: int = 5) -> dict[str, Any]:
    try:
        clean = re.sub(r"\s+", " ", text.strip())
        sentences = re.split(r"(?<=[.!?])\s+", clean)
        scored = []
        for s in sentences:
            s = s.strip()
            if len(s) < 20:
                continue
            score = len(s) + len(re.findall(r"\b(ai|model|research|new|study|report|finding|key|important)\b", s.lower())) * 10
            scored.append((score, s))
        scored.sort(key=lambda x: -x[0])
        top = [s[1] for s in scored[:max_points]]
        keywords = sorted(set(
            w.lower() for w in re.findall(r"[A-Za-z]{4,}", clean)
            if w.lower() not in {"this", "that", "with", "from", "have", "been", "which", "their", "what", "about", "would", "could", "there", "also", "than", "into", "other", "more", "some", "such", "only", "than"}
        ))[:10]
        return {
            "tool": "extract_key_points",
            "input_length": len(text),
            "key_points": top,
            "keywords": keywords,
            "point_count": len(top),
        }
    except Exception as exc:
        return {"tool": "extract_key_points", "error": type(exc).__name__, "message": str(exc)}
