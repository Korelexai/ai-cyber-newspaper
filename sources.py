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

# --- AI context terms ---------------------------------------------------
# Used as a HARD GATE: an article must reference AI/LLM/agents somewhere
# (title or summary) to be in scope at all. This is what stops generic
# cybersecurity stories (a bank breach, a ransomware gang, a random CVE)
# from being mistaken for "AI security" news just because they share
# words like "breach" or "exploit" with our keyword list.
AI_CONTEXT_TERMS = [
    "ai ", " ai", "a.i.", "artificial intelligence", "machine learning",
    "ml model", "llm", "large language model", "genai", "generative ai",
    "chatbot", "gpt", "chatgpt", "claude", "gemini", "copilot", "openai",
    "anthropic", "agentic", "ai agent", "neural network", "foundation model",
    "deep learning", "mcp", "model context protocol", "vector database",
]

# --- Keyword filter (must match at least one to be "in scope") --------
KEYWORDS = {
    # Inherently AI-specific terms — these establish AI context on their
    # own, no separate "mentions AI" check needed.
    "high": [
        "prompt injection", "jailbreak", "model poisoning", "data poisoning",
        "llm attack", "llm vulnerability", "ai supply chain",
        "adversarial prompt", "model extraction", "model theft",
        "training data leak", "ai worm", "agentic ai attack",
        "mcp vulnerability", "mcp exploit", "ai jailbreak", "model backdoor",
        "rag poisoning", "vector database leak", "adversarial attack",
    ],
    "medium": [
        "ai vulnerability", "ai security", "llm security", "genai security",
        "ai data leak", "chatbot exploit", "ai supply-chain", "ai red team",
        "llm jailbreak", "openai security", "anthropic security",
        "claude security", "gemini security", "copilot security",
        "ai platform vulnerability", "ai company hacked", "ai breach",
        "ai data breach", "ai incident",
    ],
    # Generic cyber/incident vocabulary. These ONLY count toward the score
    # if the article also matches AI_CONTEXT_TERMS (see score.py) —
    # otherwise a plain ransomware or bank-breach story would rack up
    # points just for containing "breached" or "exploit".
    "context": [
        "cve", "zero-day", "exploit", "vulnerability", "breach", "breached",
        "hacked", "data leak", "advisory", "patched", "threat actor",
        "incident", "ransomware", "compromised", "data stolen",
        "exploited in the wild", "threat actors exploit", "zero-day exploited",
        "incident disclosed", "security advisory",
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

# --- Tagging taxonomies -------------------------------------------------
# Used by tags.py to label each story with (1) which AI security area it
# falls under and (2) which industry it's about, so the newspaper can show
# short chips instead of paragraphs. First matching rule wins, so more
# specific rules are listed before general ones.
AREA_RULES = [
    ("Prompt Security", ["prompt injection", "jailbreak", "adversarial prompt", "prompt security"]),
    ("MCP Security", ["mcp vulnerability", "mcp exploit", "model context protocol", " mcp "]),
    ("Agent Security", ["agentic ai attack", "agentic ai", "ai agent", "autonomous agent", "agent security"]),
    ("Model Security", ["model poisoning", "model extraction", "model theft", "model backdoor", "model inversion"]),
    ("Data & Training Security", ["data poisoning", "training data leak", "rag poisoning", "vector database leak", "ai data leak"]),
    ("Supply Chain Security", ["ai supply chain", "ai supply-chain"]),
    ("LLM Security", ["llm attack", "llm vulnerability", "llm jailbreak", "llm security", "chatbot exploit"]),
    ("Platform Security", ["openai security", "anthropic security", "claude security", "gemini security", "copilot security", "ai platform vulnerability"]),
    ("AI Governance & Compliance", ["ai regulation", "ai policy", "ai compliance", "ai governance"]),
]
DEFAULT_AREA = "AI Security"

INDUSTRY_RULES = [
    ("BFSI", ["bank", "banking", "financial services", "fintech", "insurer", "insurance", "credit union", "payment processor"]),
    ("Healthcare", ["hospital", "healthcare", "health system", "patient data", "medical device", "clinic"]),
    ("EdTech", ["university", "school district", "edtech", "student data", "higher education", "college"]),
    ("Government & Public Sector", ["government agency", "federal agency", "state agency", "public sector", "municipal", "government"]),
    ("Retail & E-commerce", ["retailer", "e-commerce", "ecommerce", "online store", "retail chain"]),
    ("Telecom", ["telecom", "telecommunications", "mobile carrier", "isp"]),
    ("Energy & Utilities", ["power grid", "energy company", "utility company", "oil and gas"]),
    ("Manufacturing", ["manufacturer", "manufacturing plant", "industrial control system", "factory"]),
    ("Media & Entertainment", ["streaming service", "media company", "entertainment company"]),
    ("Technology", ["cloud provider", "saas company", "tech company", "software vendor", "startup"]),
]
DEFAULT_INDUSTRY = "Cross-Industry"
