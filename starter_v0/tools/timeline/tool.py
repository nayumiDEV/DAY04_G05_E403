from __future__ import annotations

from typing import Any

from tools._shared import err, twitter_get, tweets_from


def get_user_tweets(screenname: str = "", limit: int = 5) -> dict[str, Any]:
    try:
        data = twitter_get("/timeline.php", {"screenname": screenname})
        return {"tool": "get_user_tweets", "screenname": screenname, "items": tweets_from(data, limit)}
    except Exception as exc:
        return err("get_user_tweets", exc)

