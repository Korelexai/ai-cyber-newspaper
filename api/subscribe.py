"""
api/subscribe.py
-----------------
Vercel serverless function (Python runtime — any *.py file under /api/
is auto-detected as an endpoint, no extra config needed). Handles:

    POST /api/subscribe   { "name": "...", "email": "..." }

What it does:
  1. Validates the email
  2. Saves it to Supabase (table: subscribers) — service role key bypasses
     Row Level Security, since this only ever runs server-side, never in
     the browser
  3. Best-effort sends a short welcome email (failure here does NOT fail
     the subscription — if email sending breaks, people can still sign up)

Needs these set as Vercel Environment Variables (Project → Settings →
Environment Variables):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  EMAIL_SENDER               (e.g. security@korelex.ai)
  EMAIL_APP_PASSWORD         (a Gmail App Password, not your normal password)
  GOOGLE_SHEET_WEBHOOK_URL   (optional — Apps Script web app URL, see setup guide)

Only stdlib is used on purpose (urllib, smtplib) — this avoids needing a
requirements.txt for the /api folder, which keeps the Vercel build simple.
"""

from __future__ import annotations

import json
import os
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
EMAIL_LOGIN = os.environ.get("EMAIL_LOGIN", "")          # real Gmail account, used to authenticate
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")        # "From" address shown to recipients (can be an alias)
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")
GOOGLE_SHEET_WEBHOOK_URL = os.environ.get("GOOGLE_SHEET_WEBHOOK_URL", "")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _save_to_supabase(name: str, email: str) -> None:
    payload = json.dumps({"name": name, "email": email}).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/subscribers?on_conflict=email",
        data=payload,
        method="POST",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            # merge-duplicates = if this email already subscribed, just
            # update it instead of erroring (so re-subscribing is safe)
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    urllib.request.urlopen(req, timeout=8)


def _append_to_google_sheet(name: str, email: str) -> None:
    """
    Best-effort: appends a row to a Google Sheet via a tiny Google Apps
    Script "web app" (see /supabase/README or setup docs for how to
    deploy one). This is what gives you a live, always-current,
    downloadable-as-Excel view of subscribers without touching Supabase.
    Failure here never blocks the actual subscription.
    """
    if not GOOGLE_SHEET_WEBHOOK_URL:
        return
    payload = json.dumps({"name": name, "email": email}).encode()
    req = urllib.request.Request(
        GOOGLE_SHEET_WEBHOOK_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=8)

def _send_welcome_email(name: str, email: str) -> None:
    if not EMAIL_LOGIN or not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
        return  # not configured yet — skip silently, subscription still succeeds

    greeting = f"Hi {name}," if name else "Hi,"
    body = (
        f"{greeting}\n\n"
        "You're subscribed to the Korelex AI Threat Briefing.\n\n"
        "Every morning, we'll send you the top AI security stories from "
        "the last couple of days — prompt injection, model attacks, AI "
        "data breaches, and more.\n\n"
        "You can also read it any time at https://dailybriefing.korelex.ai\n\n"
        "Questions or feedback? Just reply to this email, or write to "
        "security@korelex.ai.\n\n"
        "— Korelex AI"
    )
    msg = MIMEText(body)
    msg["Subject"] = "You're subscribed — Korelex AI Threat Briefing"
    msg["From"] = EMAIL_SENDER
    msg["To"] = email

    context = ssl.create_default_context()

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
        server.starttls(context=context)
        server.login(EMAIL_LOGIN, EMAIL_APP_PASSWORD)
        server.send_message(msg)


class handler(BaseHTTPRequestHandler):
    def _respond(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw)
        except Exception:
            return self._respond(400, {"error": "Couldn't read that request."})

        name = (data.get("name") or "").strip()[:100]
        email = (data.get("email") or "").strip().lower()[:200]

        if not EMAIL_RE.match(email):
            return self._respond(400, {"error": "Please enter a valid email address."})

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return self._respond(500, {"error": "Subscriptions aren't set up yet — missing Supabase config."})

        try:
            _save_to_supabase(name, email)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="ignore")[:300]
            return self._respond(500, {"error": "Couldn't save your subscription.", "detail": detail})
        except Exception:
            return self._respond(500, {"error": "Couldn't save your subscription. Please try again."})

        # Welcome email and the Google Sheet log are both best-effort —
        # a failure in either should never make the subscription itself
        # look like it failed to the person filling out the form.
        
        try:
            _send_welcome_email(name, email)
        except Exception as e:
            print(f"[subscribe] welcome email failed: {e}")

        try:
            _append_to_google_sheet(name, email)
        except Exception as e:
            print(f"[subscribe] sheet append failed: {e}")


        return self._respond(200, {"success": True})
