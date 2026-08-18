"""
summarize.py
------------
Turns a raw article (title + RSS summary, which is often messy HTML)
into a clean 2-3 sentence "why this matters" blurb for the newspaper.

Two modes:
  - LLM mode (default if ANTHROPIC_API_KEY is set): asks Claude to
    write a tight, factual summary.
  - Fallback mode (no API key): strips HTML and trims to N sentences.
    No network call, always works, just less polished.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List

_HAS_ANTHROPIC = False
try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    pass


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fallback_summary(article: Dict, max_sentences: int = 2) -> str:
    clean = _strip_html(article.get("summary", "")) or article["title"]
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    return " ".join(sentences[:max_sentences]).strip()


def _llm_summary(article: Dict, client) -> str:
    prompt = (
        "Summarize this cybersecurity news item in 2 short sentences for a "
        "daily 'AI Cybersecurity Intelligence' briefing. Be factual and "
        "specific (who/what/impact). No preamble, no markdown, just the "
        "summary text.\n\n"
        f"Title: {article['title']}\n"
        f"Source: {article['source']}\n"
        f"Raw excerpt: {_strip_html(article.get('summary', ''))[:1200]}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ).strip()


def summarize_articles(articles: List[Dict]) -> List[Dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key) if (_HAS_ANTHROPIC and api_key) else None

    summarized = []
    for art in articles:
        try:
            blurb = _llm_summary(art, client) if client else _fallback_summary(art)
        except Exception as exc:  # noqa: BLE001 - never let a bad summary kill the run
            print(f"[summarize] Falling back for '{art['title']}': {exc}")
            blurb = _fallback_summary(art)
        summarized.append({**art, "blurb": blurb})
    return summarized
