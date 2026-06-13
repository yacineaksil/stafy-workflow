import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.dashboard.auth import require_auth, verify_login, make_session_cookie
from src.storage import database as db
from fastapi.security import HTTPBasicCredentials

log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Stafy", docs_url=None, redoc_url=None)

_refresh_running = False


# ── Filtres Jinja2 ────────────────────────────────────────────────────────────

def _priority_label(p: int) -> str:
    return {5: "CRITIQUE", 4: "HAUTE", 3: "MOYENNE", 2: "BASSE", 1: "NÉGLIGEABLE"}.get(p, "—")

def _safe_json(val) -> list:
    if not val:
        return []
    try:
        return json.loads(val) if isinstance(val, str) else val
    except Exception:
        return []

templates.env.filters["priority_label"] = _priority_label
templates.env.filters["safe_json"] = _safe_json


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    creds = HTTPBasicCredentials(username=username, password=password)
    if not verify_login(creds):
        return RedirectResponse("/login?error=1", status_code=302)

    token = make_session_cookie(username)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("stafy_session", token, httponly=True, samesite="lax", max_age=86400 * 7)
    return response


@app.get("/logout")
async def logout():
    r = RedirectResponse("/login", status_code=302)
    r.delete_cookie("stafy_session")
    return r


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(require_auth)):
    emails = db.get_emails_with_analysis(limit=50)
    briefing = db.get_latest_briefing()
    stats = db.get_dashboard_stats()

    if briefing:
        briefing["priority_list"] = _safe_json(briefing.get("priority_list"))
        briefing["alerts"] = _safe_json(briefing.get("alerts"))

    for e in emails:
        e["key_points"] = _safe_json(e.get("key_points"))

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "briefing": briefing,
        "stats": stats,
        "urgent_emails":    [e for e in emails if e.get("category") == "urgent"],
        "important_emails": [e for e in emails if e.get("category") == "important"],
        "other_emails":     [e for e in emails if e.get("category") not in ("urgent", "important")],
        "refresh_running":  _refresh_running,
        "now": datetime.now(),
        "user": user,
    })


@app.get("/email/{email_id}", response_class=HTMLResponse)
async def email_detail(request: Request, email_id: str, user: str = Depends(require_auth)):
    email = db.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email introuvable")
    email["key_points"] = _safe_json(email.get("key_points"))
    return templates.TemplateResponse("email_detail.html", {"request": request, "email": email, "user": user})


# ── Refresh ───────────────────────────────────────────────────────────────────

@app.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks, user: str = Depends(require_auth)):
    global _refresh_running
    if _refresh_running:
        return JSONResponse({"status": "already_running"})
    background_tasks.add_task(_run_refresh)
    return JSONResponse({"status": "started"})


def _run_refresh():
    global _refresh_running
    _refresh_running = True
    try:
        from src.connectors.imap import IMAPConnector
        from src.agent.email_agent import EmailAgent

        with IMAPConnector() as imap:
            emails = imap.get_messages()

        agent = EmailAgent()
        agent.run(emails)
        log.info("Refresh terminé : %d emails traités", len(emails))
    except Exception as e:
        log.error("Erreur refresh : %s", e)
    finally:
        _refresh_running = False


# ── API JSON ──────────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats(user: str = Depends(require_auth)):
    return db.get_dashboard_stats()


@app.get("/api/briefing")
async def api_briefing(user: str = Depends(require_auth)):
    b = db.get_latest_briefing()
    if b:
        b["priority_list"] = _safe_json(b.get("priority_list"))
        b["alerts"] = _safe_json(b.get("alerts"))
    return b or {}


# ── Scheduler intégré (remplace le cron) ─────────────────────────────────────

def start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    from config import settings

    scheduler = BackgroundScheduler(timezone="Europe/Paris")
    scheduler.add_job(
        _run_refresh,
        "interval",
        minutes=settings.REFRESH_INTERVAL_MINUTES,
        id="email_refresh",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler démarré — refresh toutes les %d min", settings.REFRESH_INTERVAL_MINUTES)
    return scheduler
