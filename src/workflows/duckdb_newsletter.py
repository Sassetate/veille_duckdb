"""Workflow hebdomadaire : récapitulatif des nouveautés DuckDB envoyé par email."""

import os
from datetime import datetime, timedelta, timezone

import httpx
from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai import Mistral

RECIPIENT = os.environ.get("MAIL_RECIPIENT", "johanguely@live.fr")
DAYS = 7


class NewsletterInput(BaseModel):
    recipient: str = RECIPIENT
    days: int = DAYS


class NewsletterOutput(BaseModel):
    sent: bool
    subject: str
    items_found: int


@workflows.activity()
async def fetch_duckdb_news(days: int) -> list[dict]:
    """Releases GitHub duckdb/duckdb + blog DuckDB des derniers jours."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    items: list[dict] = []
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get("https://api.github.com/repos/duckdb/duckdb/releases", headers={"Accept": "application/vnd.github+json"})
        if r.status_code == 200:
            for rel in r.json():
                published = rel.get("published_at") or rel.get("created_at")
                if published and datetime.fromisoformat(published.replace("Z", "+00:00")) >= since:
                    items.append({"type": "release", "title": str(rel.get("name") or rel.get("tag_name")), "url": rel.get("html_url", ""), "date": published, "summary": (rel.get("body") or "")[:500]})
        r = await client.get("https://duckdb.org/feed.xml")
        if r.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            for item in root.iter("item"):
                items.append({"type": "blog", "title": item.findtext("title", ""), "url": item.findtext("link", ""), "date": item.findtext("pubDate", ""), "summary": (item.findtext("description", "") or "")[:500]})
    return items


@workflows.activity()
async def summarize_news(items: list[dict], days: int) -> str:
    """Résume les nouveautés en français via l API Mistral."""
    if not items:
        return ""
    client = Mistral()
    listing = "\n".join(f"- [{i['type']}] {i['title']} ({i['date']})\n  {i['url']}\n  {i.get('summary','')[:300]}" for i in items)
    resp = client.chat.complete(model="mistral-large-latest", messages=[
        {"role": "system", "content": "Tu rédiges en français un récapitulatif concis et structuré des nouveautés DuckDB de la semaine."},
        {"role": "user", "content": f"Nouveautés DuckDB des {days} derniers jours :\n{listing}\nRédige un email de veille court et clair."}
    ])
    return resp.choices[0].message.content or ""


@workflows.activity()
async def send_email(recipient: str, subject: str, body: str) -> bool:
    """Envoi via Microsoft Graph (GRAPH_ACCESS_TOKEN requis)."""
    token = os.environ.get("GRAPH_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("GRAPH_ACCESS_TOKEN manquant")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://graph.microsoft.com/v1.0/me/sendMail", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"message": {"subject": subject, "body": {"contentType": "Text", "content": body}, "toRecipients": [{"emailAddress": {"address": recipient}}]}})
    return r.status_code == 202


@workflows.workflow.define(name="duckdb-weekly-news", workflow_display_name="Veille hebdomadaire DuckDB", workflow_description="Récapitulatif des nouveautés DuckDB de la semaine, envoyé par email.")
class DuckDBWeeklyNewsWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: NewsletterInput) -> NewsletterOutput:
        items = await fetch_duckdb_news(input.days)
        subject = f"Veille DuckDB — semaine du {datetime.now(timezone.utc).strftime('%d/%m/%Y')}"
        if not items:
            return NewsletterOutput(sent=False, subject=subject, items_found=0)
        body = await summarize_news(items, input.days)
        sent = await send_email(input.recipient, subject, body)
        return NewsletterOutput(sent=sent, subject=subject, items_found=len(items))
