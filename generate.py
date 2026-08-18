"""
generate.py
-----------
Renders the final "newspaper" artifacts:
  - output/latest.html         (always overwritten — "today's front page")
  - output/editions/YYYY-MM-DD.html  (dated archive copy)
  - output/editions/YYYY-MM-DD.json  (raw data, useful if you later
    want to pipe this into Slack/email/a real website instead of HTML)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Dict

from jinja2 import Environment, FileSystemLoader

from sources import LOOKBACK_DAYS

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
EDITIONS_DIR = os.path.join(OUTPUT_DIR, "editions")


def _json_safe(story: Dict) -> Dict:
    out = dict(story)
    out["published"] = story["published"].isoformat()
    return out


def generate_newspaper(top_stories: List[Dict]) -> str:
    os.makedirs(EDITIONS_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    edition_date = now.strftime("%Y-%m-%d")

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("newspaper.html")
    html = template.render(
        stories=top_stories,
        edition_date=edition_date,
        lookback_days=LOOKBACK_DAYS,
        generated_at=now.strftime("%Y-%m-%d %H:%M UTC"),
    )

    latest_path = os.path.join(OUTPUT_DIR, "latest.html")
    index_path = os.path.join(OUTPUT_DIR, "index.html")  # so the site's root URL works
    dated_html_path = os.path.join(EDITIONS_DIR, f"{edition_date}.html")
    dated_json_path = os.path.join(EDITIONS_DIR, f"{edition_date}.json")

    for path in (latest_path, index_path, dated_html_path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    with open(dated_json_path, "w", encoding="utf-8") as f:
        json.dump([_json_safe(s) for s in top_stories], f, indent=2)

    return latest_path
