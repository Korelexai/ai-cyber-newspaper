"""
score.py
--------
Decides:
  1. Is this article actually "AI + Cybersecurity" (in scope)?
  2. If yes, how interesting/important is it (score)?

The scoring is intentionally simple and transparent (keyword-weighted +
recency decay) rather than a black box, so you can explain/tune it
easily in your assignment writeup. Swap in an LLM-based classifier
later (see summarize.py for where an LLM call already lives) if you
want smarter scoping.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict

from sources import KEYWORDS, MIN_SCORE_THRESHOLD, LOOKBACK_DAYS, PREFER_CATEGORY_ORDER, TOP_N


def _text_of(article: Dict) -> str:
    return f"{article['title']} {article['summary']}".lower()


def keyword_score(article: Dict) -> int:
    text = _text_of(article)
    score = 0
    for kw in KEYWORDS["high"]:
        if kw in text:
            score += 3
    for kw in KEYWORDS["medium"]:
        if kw in text:
            score += 2
    # "context" words only count if the text also mentions AI/LLM/model,
    # otherwise "vulnerability" alone would match every generic CVE post.
    mentions_ai = any(t in text for t in ["ai ", " ai", "llm", "model", "chatbot", "genai", "gpt", "claude", "gemini", "copilot"])
    if mentions_ai:
        for kw in KEYWORDS["context"]:
            if kw in text:
                score += 1
    return score


def recency_score(article: Dict, now: datetime) -> float:
    age_hours = max((now - article["published"]).total_seconds() / 3600, 0)
    # Fresh articles get a bonus that decays over the lookback window.
    lookback_hours = LOOKBACK_DAYS * 24
    return max(0.0, (lookback_hours - age_hours) / lookback_hours) * 3


def is_within_lookback(article: Dict, now: datetime) -> bool:
    age_days = (now - article["published"]).total_seconds() / 86400
    return 0 <= age_days <= LOOKBACK_DAYS


def score_and_filter(articles: List[Dict]) -> List[Dict]:
    now = datetime.now(timezone.utc)
    scored = []
    for art in articles:
        if not is_within_lookback(art, now):
            continue

        kw_score = keyword_score(art)
        if kw_score < MIN_SCORE_THRESHOLD:
            continue  # out of scope (not AI+cybersecurity enough)

        total = kw_score + recency_score(art, now) + art.get("source_weight", 1.0)
        art = {**art, "score": round(total, 2), "keyword_score": kw_score}
        scored.append(art)

    scored.sort(key=lambda a: a["score"], reverse=True)
    return scored


def pick_top_stories(scored_articles: List[Dict], top_n: int = TOP_N) -> List[Dict]:
    """
    Fills the front page "news first": every breaking-news article
    (category='news') is considered before any research paper. Research
    papers (category='research', e.g. arXiv) only fill leftover slots
    if there genuinely isn't enough real news that day.

    Within each category, articles stay sorted by score (already sorted
    coming in from score_and_filter).
    """
    picked: List[Dict] = []
    remaining = list(scored_articles)

    for category in PREFER_CATEGORY_ORDER:
        if len(picked) >= top_n:
            break
        for art in remaining:
            if len(picked) >= top_n:
                break
            if art.get("category") == category and art not in picked:
                picked.append(art)
        remaining = [a for a in remaining if a not in picked]

    return picked[:top_n]


if __name__ == "__main__":
    from fetch import fetch_all

    ranked = score_and_filter(fetch_all())
    print(f"{len(ranked)} in-scope articles in the last {LOOKBACK_DAYS} days")
    for a in ranked[:10]:
        print(f"{a['score']:>5.2f}  {a['source']:<28} {a['title']}")
