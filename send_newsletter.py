"""
send_newsletter.py
-------------------
Sends the day's top stories to every subscriber, by email.

Runs as an optional extra step at the end of main.py — only when the
SEND_NEWSLETTER environment variable is set to "true" (so local test
runs of `python main.py` never accidentally email real subscribers;
only the scheduled GitHub Actions run does).

Needs these environment variables (set as GitHub Actions secrets):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  EMAIL_SENDER          (e.g. security@korelex.ai)
  EMAIL_APP_PASSWORD    (a Gmail App Password)

Uses only the `requests` library (already in requirements.txt) plus
Python's built-in smtplib/email — no new dependencies.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
EMAIL_LOGIN = os.environ.get("EMAIL_LOGIN", "")          # real Gmail account, used to authenticate
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")        # "From" address shown to recipients (can be an alias)
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")

SITE_URL = "https://dailybriefing.korelex.ai"


def fetch_subscribers() -> List[Dict]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("[send_newsletter] Supabase not configured — skipping.")
        return []

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/subscribers",
        params={"select": "name,email", "unsubscribed": "eq.false"},
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _build_html(top_stories: List[Dict], edition_date: str) -> str:
    tier_labels = ["CRITICAL", "HIGH", "NOTABLE"]
    tier_colors = ["#ff4d6a", "#ffb343", "#4fc3e0"]

    story_blocks = []
    for i, story in enumerate(top_stories):
        label = tier_labels[i] if i < 3 else "MONITORED"
        color = tier_colors[i] if i < 3 else "#6b7280"
        story_blocks.append(f"""
        <tr>
          <td style="padding: 0 0 24px 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="background:#12151c; border-left:3px solid {color}; border-radius:8px;">
              <tr><td style="padding: 18px 20px;">
                <div style="font-family: monospace; font-size:11px; letter-spacing:0.08em; color:{color}; text-transform:uppercase; margin-bottom:8px;">
                  {label} &middot; {story.get('area_tag', 'AI Security')}
                </div>
                <div style="font-family: Georgia, serif; font-size:18px; font-weight:bold; color:#e9ecf3; margin-bottom:8px; line-height:1.3;">
                  <a href="{story['link']}" style="color:#e9ecf3; text-decoration:none;">{story['title']}</a>
                </div>
                <div style="font-family: monospace; font-size:11px; color:#8890a3; margin-bottom:10px;">
                  {story['source']}
                </div>
                <div style="font-family: Arial, sans-serif; font-size:14px; color:#b7bcc9; line-height:1.55; margin-bottom:10px;">
                  {story.get('blurb', '')}
                </div>
                <a href="{story['link']}" style="font-family: monospace; font-size:12px; color:#5e7cff; text-decoration:none;">Read full report &rarr;</a>
              </td></tr>
            </table>
          </td>
        </tr>""")

    return f"""\
<html>
<body style="margin:0; padding:0; background:#0a0c11;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0c11; padding: 32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;">
        <tr><td style="padding-bottom: 24px;">
          <div style="font-family: monospace; font-size:12px; letter-spacing:0.14em; color:#e9ecf3;">SIGNAL &middot; KORELEX AI</div>
          <div style="font-family: Georgia, serif; font-size:26px; font-weight:bold; color:#e9ecf3; margin-top:8px;">AI Threat Briefing</div>
          <div style="font-family: Arial, sans-serif; font-size:13px; color:#8890a3; margin-top:6px;">{edition_date}</div>
        </td></tr>
        {''.join(story_blocks)}
        <tr><td style="padding-top: 8px; text-align:center;">
          <a href="{SITE_URL}" style="font-family: Arial, sans-serif; font-size:13px; color:#5e7cff; text-decoration:none;">View full briefing online &rarr;</a>
        </td></tr>
        <tr><td style="padding-top: 32px; text-align:center; font-family: monospace; font-size:11px; color:#565d70;">
          Sent by Korelex AI &middot; Questions or want to stop receiving this? Reply or write to security@korelex.ai
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

def send_daily_email(top_stories: List[Dict], edition_date: str) -> None:
    if not EMAIL_LOGIN or not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
        print("[send_newsletter] Email sender not configured — skipping.")
        return
    
    subscribers = fetch_subscribers()
    if not subscribers:
        print("[send_newsletter] No subscribers to email.")
        return

    html = _build_html(top_stories, edition_date)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Threat Briefing — {edition_date}"
    msg["From"] = EMAIL_SENDER
    # Recipients go in Bcc so subscribers can't see each other's emails.
    # "To" is set to the sender itself, which is normal practice for a
    # Bcc-only send.
    msg["To"] = EMAIL_SENDER
    msg.attach(MIMEText(html, "html"))

    recipient_emails = [s["email"] for s in subscribers if s.get("email")]

    context = ssl.create_default_context()
    
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls(context=context)
        server.login(EMAIL_LOGIN, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_emails, msg.as_string())

    print(f"[send_newsletter] Sent to {len(recipient_emails)} subscriber(s).")
