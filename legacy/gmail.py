import os
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from email.utils import parseaddr, parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.models.email import Email
from config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailConnector:
    def __init__(self):
        self.service = None
        self.user_email = None

    def authenticate(self) -> bool:
        creds = None
        token_path = Path(settings.GMAIL_TOKEN_FILE)
        credentials_path = Path(settings.GMAIL_CREDENTIALS_FILE)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        f"Fichier credentials.json introuvable. "
                        f"Lancez 'python setup_oauth.py' pour configurer Gmail."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            token_path.write_text(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

        profile = self.service.users().getProfile(userId="me").execute()
        self.user_email = profile.get("emailAddress", "")
        return True

    def get_messages(
        self,
        max_results: int = None,
        query: str = "is:unread",
        label_ids: list[str] = None,
    ) -> list[Email]:
        if not self.service:
            raise RuntimeError("Non authentifié. Appelez authenticate() d'abord.")

        max_results = max_results or settings.MAX_EMAILS_PER_FETCH
        params = {
            "userId": "me",
            "maxResults": max_results,
            "q": query,
        }
        if label_ids:
            params["labelIds"] = label_ids

        try:
            result = self.service.users().messages().list(**params).execute()
            messages = result.get("messages", [])
            emails = []
            for msg in messages:
                email = self._get_message_detail(msg["id"])
                if email:
                    emails.append(email)
            return emails
        except HttpError as e:
            raise RuntimeError(f"Erreur Gmail API: {e}")

    def _get_message_detail(self, message_id: str) -> Optional[Email]:
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            subject = headers.get("subject", "(Sans objet)")
            from_raw = headers.get("from", "")
            to_raw = headers.get("to", "")
            date_str = headers.get("date", "")

            sender_name, sender_email = parseaddr(from_raw)
            if not sender_name:
                sender_name = sender_email

            try:
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            body = self._extract_body(msg.get("payload", {}))
            snippet = msg.get("snippet", "")
            labels = msg.get("labelIds", [])
            is_read = "UNREAD" not in labels

            return Email(
                id=message_id,
                thread_id=msg.get("threadId", message_id),
                subject=subject,
                sender=sender_name or sender_email,
                sender_email=sender_email,
                recipient=to_raw,
                date=date,
                body=body[:5000],
                snippet=snippet,
                is_read=is_read,
                labels=labels,
            )
        except Exception:
            return None

    def _extract_body(self, payload: dict) -> str:
        body = ""
        if payload.get("body", {}).get("data"):
            body = self._decode_base64(payload["body"]["data"])
        elif payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    if part.get("body", {}).get("data"):
                        body = self._decode_base64(part["body"]["data"])
                        break
            if not body:
                for part in payload.get("parts", []):
                    if part.get("mimeType") == "text/html":
                        if part.get("body", {}).get("data"):
                            html = self._decode_base64(part["body"]["data"])
                            body = re.sub(r"<[^>]+>", " ", html)
                            body = re.sub(r"\s+", " ", body).strip()
                            break
        return body

    def _decode_base64(self, data: str) -> str:
        try:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        except Exception:
            return ""

    def mark_as_read(self, message_id: str) -> bool:
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            return True
        except HttpError:
            return False

    def archive(self, message_id: str) -> bool:
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["INBOX"]},
            ).execute()
            return True
        except HttpError:
            return False

    def send_reply(self, thread_id: str, to: str, subject: str, body: str) -> bool:
        import email as email_lib
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            self.service.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": thread_id},
            ).execute()
            return True
        except HttpError:
            return False
