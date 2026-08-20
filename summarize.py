"""
summarize.py
------------
Turns a raw article (title + RSS summary, which is often messy HTML)
into TWO things for the newspaper card:

  - blurb:          2 sentences, factual, "what happened"
  - why_it_matters: 1-2 sentences, "so what" — why it matters and what
                     a reader should take away or do about it

Two modes:
  - LLM mode (default if ANTHROPIC_API_KEY is set): asks Claude for
    both, as JSON.
  - Fallback mode (no API key): blurb is trimmed straight from the
    article; why_it_matters is a short templated line built from the
    story's threat/industry tags (still useful, just less specific).
"""

from __future__ import annotations

import json
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


def _fallback_why_it_matters(article: Dict) -> str:
    # Uses tags if they've already been applied (tag_articles runs
    # before summarize_articles in main.py) — falls back to a generic
    # line if tags aren't present yet (e.g. this function is called
    # standalone/out of order).
    area = article.get("area_tag", "AI security")
    industry = article.get("industry_tag")
    if industry and industry != "Cross-Industry":
        return (f"This is a {area.lower()} issue with direct relevance to {industry} "
                f"organizations — teams in that space should check their own exposure.")
    return (f"This falls under {area.lower()} — worth a quick check against your own "
            f"AI systems for similar exposure.")


def _llm_summary_and_impact(article: Dict, client) -> Dict[str, str]:
    prompt = (
        "You are writing two short pieces for a daily AI-security briefing card.\n\n"
        "1. \"summary\": 2 factual sentences on what happened (who/what/impact). "
        "No preamble.\n"
        "2. \"why_it_matters\": 1-2 sentences on why this matters and what a reader "
        "(a security or AI team) should take away or watch out for. Be concrete and "
        "actionable, not generic.\n\n"
        "Respond with ONLY a JSON object, no markdown fences, in exactly this shape:\n"
        '{"summary": "...", "why_it_matters": "..."}\n\n'
        f"Title: {article['title']}\n"
        f"Source: {article['source']}\n"
        f"Raw excerpt: {_strip_html(article.get('summary', ''))[:1200]}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ).strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    data = json.loads(raw)
    return {
        "blurb": data["summary"].strip(),
        "why_it_matters": data["why_it_matters"].strip(),
    }


def summarize_articles(articles: List[Dict]) -> List[Dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key) if (_HAS_ANTHROPIC and api_key) else None

    summarized = []
    for art in articles:
        try:
            if client:
                result = _llm_summary_and_impact(art, client)
            else:
                result = {
                    "blurb": _fallback_summary(art),
                    "why_it_matters": _fallback_why_it_matters(art),
                }
        except Exception as exc:  # noqa: BLE001 - never let a bad summary kill the run
            print(f"[summarize] Falling back for '{art['title']}': {exc}")
            result = {
                "blurb": _fallback_summary(art),
                "why_it_matters": _fallback_why_it_matters(art),
            }
        summarized.append({**art, **result})
    return summarized
