import secrets
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from itsdangerous import URLSafeTimedSerializer, BadSignature

from config import settings

_security = HTTPBasic(auto_error=False)
_signer = URLSafeTimedSerializer(settings.SECRET_KEY)


def _sign_session(username: str) -> str:
    return _signer.dumps(username, salt="stafy-session")


def _unsign_session(token: str, max_age: int = 86400 * 7) -> str | None:
    try:
        return _signer.loads(token, salt="stafy-session", max_age=max_age)
    except BadSignature:
        return None


def require_auth(request: Request) -> str:
    """Dépendance FastAPI — vérifie le cookie de session."""
    token = request.cookies.get("stafy_session")
    if token:
        user = _unsign_session(token)
        if user:
            return user
    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": "/login"},
    )


def verify_login(credentials: HTTPBasicCredentials) -> bool:
    ok_user = secrets.compare_digest(
        credentials.username.encode(), settings.DASHBOARD_USERNAME.encode()
    )
    ok_pass = secrets.compare_digest(
        credentials.password.encode(), settings.DASHBOARD_PASSWORD.encode()
    )
    return ok_user and ok_pass


def make_session_cookie(username: str) -> str:
    return _sign_session(username)
