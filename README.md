# AI Cybersecurity Intelligence Bot

A daily crawler/bot that answers one question every morning:

> "What are the top 3 AI cybersecurity incidents/news/events from the last ~2 days?"

It scans security news feeds, Hacker News, and arXiv, keeps only stories
at the **intersection of AI and cybersecurity** (prompt injection, model
poisoning, AI supply-chain attacks, AI-related CVEs, etc. — not generic
infosec, not generic AI news), ranks them, and renders a newspaper-style
HTML front page with the top 3.

Inspired by [The Daily Diff](https://github.com/arpitbbhayani/the-daily-diff)
(chronological, ranked, newspaper-style editions) but rebuilt in Python
and scoped specifically to AI security.

## How it works (pipeline)

```
sources.py   -> where to look (RSS feeds, HN search queries) + keyword scope
fetch.py     -> pulls raw articles from every source, normalizes them
score.py     -> filters to "last 2 days" + "AI+cybersecurity" and ranks by score
summarize.py -> writes a 2-sentence "why this matters" blurb per story
                (uses Claude if ANTHROPIC_API_KEY is set, else a simple
                 fallback that just trims the article's own summary)
generate.py  -> renders templates/newspaper.html into output/latest.html
                + a dated archive copy in output/editions/
main.py      -> runs the whole pipeline end-to-end
```

Run it, and you get `output/latest.html` — open it in a browser and
you have your "newspaper."

## Step 1 — Install

```bash
git clone <this-repo>
cd ai-cyber-newspaper
pip install -r requirements.txt
```

## Step 2 — (Optional) Enable AI-written summaries

Without an API key, summaries fall back to a trimmed version of the
article's own snippet — it still works, just less polished.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Step 3 — Run it

```bash
python main.py
```

You'll see console output like:

```
[1/4] Fetching articles from all sources...
      -> 143 raw articles fetched
[2/4] Scoring and filtering for AI+cybersecurity relevance...
      -> 7 in-scope articles in the lookback window
[3/4] Summarizing top 3 stories...
[4/4] Generating newspaper...
Done. Edition written to: output/latest.html
```

Open `output/latest.html` in a browser.

## Step 4 — Automate it ("every morning")

A ready-to-go GitHub Actions workflow is included at
`.github/workflows/daily.yml`. It:

1. Runs every day at 07:00 UTC (edit the `cron:` line for your timezone)
2. Installs dependencies and runs `main.py`
3. Commits the new `output/` files back to the repo

To use it:

1. Push this repo to GitHub.
2. (Optional) Add `ANTHROPIC_API_KEY` under **Settings → Secrets and
   variables → Actions → New repository secret**.
3. Enable GitHub Pages on the repo (**Settings → Pages → Source:
   `main` branch, `/output` folder`**) if you want `latest.html` to be
   viewable at a public URL — this gives you a live, always-current
   "newspaper" website with zero extra hosting, exactly like `tdd.cat`
   does for The Daily Diff.
4. You can also trigger it manually anytime from the **Actions** tab
   (`workflow_dispatch`).

If you'd rather get it as a Slack/email message instead of (or in
addition to) a webpage, that's a small addition to `main.py`: after
`generate_newspaper()`, post `top_stories` to a Slack webhook URL or
send an email via SMTP — say the word and I'll add that module too.

## Tuning the scope

Everything that defines "in scope" lives in `sources.py`:

- `RSS_SOURCES` — which feeds to pull from
- `HN_SEARCH_QUERIES` — what to search for on Hacker News
- `KEYWORDS` — the AI+cybersecurity keyword list (high/medium/context
  weighted) used by `score.py` to decide relevance
- `MIN_SCORE_THRESHOLD` — how strict the filter is
- `LOOKBACK_DAYS` — the "~2 days" window
- `TOP_N` — how many stories make the front page (default 3)

If your manager wants a different scope emphasis (e.g. more weight on
CVEs vs. research papers), this is the only file you need to touch.

## Extending it

- **Smarter scope detection**: replace the keyword scorer in `score.py`
  with a Claude call that classifies "is this AI+cybersecurity, yes/no"
  — more accurate, costs a few cents/day in API calls.
- **More sources**: add entries to `RSS_SOURCES` in `sources.py` — any
  standard RSS/Atom feed works out of the box.
- **De-duplication across near-identical stories** (e.g. the same CVE
  covered by 5 outlets): currently deduped by exact link only; you
  could add title-similarity matching (e.g. `difflib`) if outlets
  cover the same incident with different URLs.
