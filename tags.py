"""
tags.py
-------
Adds two short "chip" labels to each story so readers can scan the front
page without reading full paragraphs:

  - area_tag:     which part of AI security this falls under
                   (Prompt Security, MCP Security, Agent Security, ...)
  - industry_tag: which industry/sector this news is about
                   (BFSI, EdTech, Healthcare, ... or "Cross-Industry"
                   if no specific industry is mentioned)

Pure keyword matching against sources.AREA_RULES / INDUSTRY_RULES —
first matching rule wins, so ordering in sources.py matters (specific
rules first, general ones last).
"""

from __future__ import annotations

from typing import Dict, List

from sources import AREA_RULES, DEFAULT_AREA, INDUSTRY_RULES, DEFAULT_INDUSTRY


def _text_of(article: Dict) -> str:
    return f"{article.get('title', '')} {article.get('summary', '')} {article.get('blurb', '')}".lower()


def tag_area(article: Dict) -> str:
    text = _text_of(article)
    for label, keywords in AREA_RULES:
        if any(kw in text for kw in keywords):
            return label
    return DEFAULT_AREA


def tag_industry(article: Dict) -> str:
    text = _text_of(article)
    for label, keywords in INDUSTRY_RULES:
        if any(kw in text for kw in keywords):
            return label
    return DEFAULT_INDUSTRY


def tag_articles(articles: List[Dict]) -> List[Dict]:
    """Adds 'area_tag' and 'industry_tag' to each article dict."""
    return [
        {**art, "area_tag": tag_area(art), "industry_tag": tag_industry(art)}
        for art in articles
    ]


if __name__ == "__main__":
    from fetch import fetch_all
    from score import score_and_filter, pick_top_stories
    from sources import TOP_N

    ranked = score_and_filter(fetch_all())
    top = tag_articles(pick_top_stories(ranked, TOP_N))
    for a in top:
        print(f"[{a['area_tag']:<26}] [{a['industry_tag']:<24}] {a['title']}")
