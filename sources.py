"""
sources.py
----------
Everything about WHERE we look and WHAT we consider "in scope".

Scope (per assignment): AI + Cybersecurity intersection only — not
generic infosec news, and not generic AI news. An article must be
about things like: AI model vulnerabilities, LLM attacks, prompt
injection, AI data leakage, model poisoning, AI supply-chain attacks,
vulnerabilities in AI platforms, attacks involving AI systems, AI
security incidents at companies, new AI security threats, or
AI-related CVEs/advisories.

NOTE ON "news" vs "research":
Every source has a "category": either "news" (breaking incidents,
breaches, advisories — what a manager usually means by "AI security
news") or "research" (arXiv-style academic papers). score.py prefers
"news" articles for the final top 3, and only reaches for "research"
ones to fill remaining slots if there isn't enough real news that day.
"""

# --- RSS / Atom feeds -------------------------------------------------
RSS_SOURCES = [
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "weight": 1.2, "category": "news"},
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/", "weight": 1.2, "category": "news"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml", "weight": 1.1, "category": "news"},
    {"name": "SecurityWeek", "url": "https://www.securityweek.com/feed/", "weight": 1.1, "category": "news"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "weight": 1.2, "category": "news"},
    {"name": "The Register (Security)", "url": "https://www.theregister.com/security/headlines.atom", "weight": 1.0, "category": "news"},
    {"name": "Google Cloud Threat Intelligence", "url": "https://cloud.google.com/blog/topics/threat-intelligence/rss/", "weight": 1.1, "category": "news"},
    {"name": "Wiz Blog", "url": "https://www.wiz.io/blog/rss.xml", "weight": 1.0, "category": "news"},
    {"name": "Simon Willison (prompt injection / LLM security)", "url": "https://simonwillison.net/atom/everything/", "weight": 1.0, "category": "news"},
    {"name": "NIST NVD CVE Feed", "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml", "weight": 0.9, "category": "news"},
    {"name": "SC Media", "url": "https://www.scworld.com/feed", "weight": 1.0, "category": "news"},
    {"name": "The Record (Recorded Future News)", "url": "https://therecord.media/feed", "weight": 1.1, "category": "news"},
    {"name": "arXiv cs.CR (Cryptography & Security)", "url": "http://export.arxiv.org/rss/cs.CR", "weight": 0.5, "category": "research"},
]

# --- Hacker News (via Algolia search API, no key needed) --------------
HN_SEARCH_QUERIES = [
    "prompt injection",
    "LLM vulnerability",
    "AI security breach",
    "model poisoning",
    "AI supply chain attack",
    "AI data breach",
    "AI company hacked",
]
HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_CATEGORY = "news"

# --- Keyword filter (must match at least one to be "in scope") --------
KEYWORDS = {
    "high": [
        "prompt injection", "jailbreak", "model poisoning", "data poisoning",
        "llm attack", "llm vulnerability", "ai supply chain",
        "adversarial prompt", "model extraction", "model theft",
        "training data leak", "ai worm", "agentic ai attack",
        "mcp vulnerability", "mcp exploit",
        # breaking-incident specific
        "ai company hacked", "ai breach", "ai data breach",
        "breached", "hacked", "exploited in the wild",
        "ransomware", "threat actors exploit", "data stolen",
        "compromised", "zero-day exploited",
    ],
    "medium": [
        "ai vulnerability", "ai security", "llm security", "genai security",
        "ai data leak", "chatbot exploit", "ai supply-chain",
        "adversarial attack", "model backdoor", "ai red team",
        "llm jailbreak", "rag poisoning", "vector database leak",
        "openai security", "anthropic security", "claude security",
        "gemini security", "copilot security", "ai platform vulnerability",
        "incident disclosed", "security advisory",
    ],
    "context": [
        "cve", "zero-day", "exploit", "vulnerability", "breach",
        "data leak", "advisory", "patched", "threat actor", "incident",
    ],
}

# Minimum score for an article to be considered in-scope at all
MIN_SCORE_THRESHOLD = 2

# How far back to look, per the assignment ("last ~2 days")
LOOKBACK_DAYS = 2

# How many stories the final "newspaper" front page shows
TOP_N = 3

# Prefer "news" category articles over "research" ones when filling
# the top N — research papers only fill leftover slots.
PREFER_CATEGORY_ORDER = ["news", "research"]
