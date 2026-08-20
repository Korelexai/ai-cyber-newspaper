"""
main.py
-------
Entry point. Run this every morning (locally via cron, or via the
included GitHub Actions workflow) to produce today's edition.

    python main.py

Pipeline:
    fetch_all()          -> raw articles from RSS + Hacker News
    score_and_filter()   -> keep only in-scope AI+cybersecurity items,
                             ranked by score
    top N                -> take the top 3 (sources.TOP_N)
    tag_articles()       -> add area_tag (Prompt Security, MCP Security, ...)
                             and industry_tag (BFSI, EdTech, ...) chips
    summarize_articles() -> add "blurb" (what happened) and
                             "why_it_matters" (so what / takeaway)
    generate_newspaper() -> write output/latest.html (+ dated archive)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from fetch import fetch_all
from score import score_and_filter, pick_top_stories
from summarize import summarize_articles
from tags import tag_articles
from generate import generate_newspaper
from sources import TOP_N


def run() -> None:
    print("[1/4] Fetching articles from all sources...")
    raw = fetch_all()
    print(f"      -> {len(raw)} raw articles fetched")

    print("[2/4] Scoring and filtering for AI+cybersecurity relevance...")
    ranked = score_and_filter(raw)
    print(f"      -> {len(ranked)} in-scope articles in the lookback window")

    if not ranked:
        print("No in-scope articles found in the lookback window. Exiting without "
              "overwriting the previous edition.")
        sys.exit(0)

    top_stories = pick_top_stories(ranked, TOP_N)
    print(f"[3/4] Tagging and summarizing top {len(top_stories)} stories...")
    top_stories = tag_articles(top_stories)
    top_stories = summarize_articles(top_stories)

    print("[4/4] Generating newspaper...")
    path = generate_newspaper(top_stories)
    print(f"Done. Edition written to: {path}")

    print("\nToday's top stories:")
    for i, story in enumerate(top_stories, start=1):
        print(f"  {i}. [{story['source']}] {story['title']}")
        print(f"     {story['link']}")

    # Optional: email the day's briefing to subscribers. Only runs when
    # SEND_NEWSLETTER=true is set (the scheduled GitHub Action sets this;
    # local test runs of `python main.py` don't, so you never accidentally
    # email real subscribers while testing).
    if os.environ.get("SEND_NEWSLETTER", "").lower() == "true":
        print("\n[Newsletter] Sending daily email to subscribers...")
        try:
            from send_newsletter import send_daily_email
            edition_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            send_daily_email(top_stories, edition_date)
        except Exception as exc:  # noqa: BLE001 - never let a mail failure break the whole run
            print(f"[Newsletter] Failed to send: {exc}")


if __name__ == "__main__":
    run()
