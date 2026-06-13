import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.storage import database as db

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Stafy – Assistante Exécutive Email", docs_url=None, redoc_url=None)

_refresh_running = False


def _priority_label(priority: int) -> str:
    labels = {5: "CRITIQUE", 4: "HAUTE", 3: "MOYENNE", 2: "BASSE", 1: "NÉGLIGEABLE"}
    return labels.get(priority, "—")


def _category_color(category: str) -> str:
    colors = {
        "urgent": "red",
        "important": "orange",
        "normal": "blue",
        "newsletter": "purple",
        "spam": "gray",
    }
    return colors.get(category, "gray")


templates.env.filters["priority_label"] = _priority_label
templates.env.filters["category_color"] = _category_color


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    emails = db.get_emails_with_analysis(limit=50)
    briefing = db.get_latest_briefing()
    stats = db.get_dashboard_stats()

    if briefing:
        briefing["priority_list"] = json.loads(briefing.get("priority_list", "[]"))
        briefing["alerts"] = json.loads(briefing.get("alerts", "[]"))

    for email in emails:
        if email.get("key_points"):
            email["key_points"] = json.loads(email["key_points"])

    urgent_emails = [e for e in emails if e.get("category") == "urgent"]
    important_emails = [e for e in emails if e.get("category") == "important"]
    other_emails = [e for e in emails if e.get("category") not in ("urgent", "important")]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "briefing": briefing,
            "stats": stats,
            "urgent_emails": urgent_emails,
            "important_emails": important_emails,
            "other_emails": other_emails,
            "refresh_running": _refresh_running,
            "now": datetime.now(),
        },
    )


@app.get("/email/{email_id}", response_class=HTMLResponse)
async def email_detail(request: Request, email_id: str):
    email = db.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email introuvable")

    if email.get("key_points"):
        email["key_points"] = json.loads(email["key_points"])

    return templates.TemplateResponse(
        "email_detail.html",
        {"request": request, "email": email},
    )


@app.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    global _refresh_running
    if _refresh_running:
        return JSONResponse({"status": "already_running"})

    background_tasks.add_task(_run_refresh)
    return JSONResponse({"status": "started"})


async def _run_refresh():
    global _refresh_running
    _refresh_running = True
    try:
        from src.connectors.gmail import GmailConnector
        from src.agent.email_agent import EmailAgent

        gmail = GmailConnector()
        gmail.authenticate()
        emails = gmail.get_messages()

        agent = EmailAgent()
        agent.run(emails)
    finally:
        _refresh_running = False


@app.get("/api/stats")
async def api_stats():
    return db.get_dashboard_stats()


@app.get("/api/briefing")
async def api_briefing():
    briefing = db.get_latest_briefing()
    if briefing:
        briefing["priority_list"] = json.loads(briefing.get("priority_list", "[]"))
        briefing["alerts"] = json.loads(briefing.get("alerts", "[]"))
    return briefing or {}
