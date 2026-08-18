"""
fetch.py
--------
Pulls raw articles from every source in sources.py and normalizes them
into a common dict shape:

    {
        "title": str,
        "link": str,
        "summary": str,
        "source": str,
        "published": datetime (UTC, tz-aware),
    }

No filtering or scoring happens here — that's score.py's job. This
file only knows how to talk to feeds/APIs and clean up the result.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Dict

import feedparser
import requests

from sources import RSS_SOURCES, HN_SEARCH_QUERIES, HN_ALGOLIA_URL, HN_CATEGORY

USER_AGENT = "ai-cyber-newspaper-bot/1.0 (+https://example.com; contact: you@example.com)"
REQUEST_TIMEOUT = 15


def _to_utc(struct_time) -> datetime:
    """feedparser gives a time.struct_time in UTC already for *_parsed fields."""
    if struct_time is None:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(time.mktime(struct_time), tz=timezone.utc)


def fetch_rss() -> List[Dict]:
    articles = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(
                source["url"],
                request_headers={"User-Agent": USER_AGENT},
            )
        except Exception as exc:  # noqa: BLE001 - we want to keep going on any single-feed failure
            print(f"[fetch_rss] Failed to fetch {source['name']}: {exc}")
            continue

        for entry in feed.entries:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            articles.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "summary": (entry.get("summary") or entry.get("description") or "").strip(),
                "source": source["name"],
                "source_weight": source["weight"],
                "category": source.get("category", "news"),
                "published": _to_utc(published),
            })
    return articles


def fetch_hacker_news() -> List[Dict]:
    articles = []
    for query in HN_SEARCH_QUERIES:
        try:
            resp = requests.get(
                HN_ALGOLIA_URL,
                params={"query": query, "tags": "story", "hitsPerPage": 20},
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"[fetch_hacker_news] Failed query '{query}': {exc}")
            continue

        for hit in data.get("hits", []):
            created_at = hit.get("created_at")
            try:
                published = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:  # noqa: BLE001
                published = datetime.now(timezone.utc)

            link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            articles.append({
                "title": hit.get("title", "").strip(),
                "link": link,
                "summary": "",  # HN stories rarely have a body; title carries the signal
                "source": "Hacker News",
                "source_weight": 0.9,
                "category": HN_CATEGORY,
                "published": published,
            })
    return articles


def fetch_all() -> List[Dict]:
    articles = fetch_rss() + fetch_hacker_news()
    # De-duplicate by link (same story often appears via multiple queries/feeds)
    seen = set()
    deduped = []
    for art in articles:
        key = art["link"] or art["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(art)
    return deduped


if __name__ == "__main__":
    items = fetch_all()
    print(f"Fetched {len(items)} raw articles")
    for a in items[:5]:
        print("-", a["source"], "|", a["title"])
