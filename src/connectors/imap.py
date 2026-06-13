import imaplib
import email as email_lib
import re
from datetime import datetime
from email.header import decode_header as _decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional

from src.models.email import Email
from config import settings


def _decode_str(raw) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    parts = _decode_header(raw)
    decoded = []
    for chunk, charset in parts:
        if isinstance(chunk, bytes):
            decoded.append(chunk.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(str(chunk))
    return " ".join(decoded)


def _extract_body(msg: email_lib.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = part.get("Content-Disposition", "")
            if ct == "text/plain" and "attachment" not in cd:
                charset = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(charset, errors="replace")
                break
        if not body:
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    html = part.get_payload(decode=True).decode(charset, errors="replace")
                    body = re.sub(r"<[^>]+>", " ", html)
                    body = re.sub(r"\s+", " ", body).strip()
                    break
    else:
        charset = msg.get_content_charset() or "utf-8"
        body = msg.get_payload(decode=True).decode(charset, errors="replace")

    return body[:5000]


class IMAPConnector:
    def __init__(self):
        self.conn: Optional[imaplib.IMAP4_SSL | imaplib.IMAP4] = None
        self.user_email: str = settings.IMAP_USERNAME

    def connect(self) -> bool:
        if settings.IMAP_SSL:
            self.conn = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        else:
            self.conn = imaplib.IMAP4(settings.IMAP_HOST, settings.IMAP_PORT)
        self.conn.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        return True

    def disconnect(self):
        if self.conn:
            try:
                self.conn.logout()
            except Exception:
                pass

    def get_messages(
        self,
        folder: str = "INBOX",
        max_results: int = None,
        unread_only: bool = True,
    ) -> list[Email]:
        max_results = max_results or settings.MAX_EMAILS_PER_FETCH

        self.conn.select(folder)
        criterion = "UNSEEN" if unread_only else "ALL"
        _, data = self.conn.search(None, criterion)

        ids = data[0].split()
        ids = ids[-max_results:] if len(ids) > max_results else ids
        ids = list(reversed(ids))

        emails = []
        for uid in ids:
            e = self._fetch_message(uid)
            if e:
                emails.append(e)
        return emails

    def _fetch_message(self, uid: bytes) -> Optional[Email]:
        try:
            _, data = self.conn.fetch(uid, "(RFC822)")
            raw = data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject = _decode_str(msg.get("Subject", "(Sans objet)"))
            from_raw = _decode_str(msg.get("From", ""))
            to_raw = _decode_str(msg.get("To", ""))
            date_str = msg.get("Date", "")
            msg_id = msg.get("Message-ID", uid.decode())

            sender_name, sender_email_addr = parseaddr(from_raw)
            if not sender_name:
                sender_name = sender_email_addr

            try:
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            body = _extract_body(msg)
            snippet = body[:200].replace("\n", " ").strip()

            return Email(
                id=msg_id.strip("<>"),
                thread_id=msg.get("References", msg_id).split()[-1].strip("<>"),
                subject=subject,
                sender=sender_name,
                sender_email=sender_email_addr,
                recipient=to_raw,
                date=date,
                body=body,
                snippet=snippet,
                is_read=False,
                labels=[],
            )
        except Exception:
            return None

    def mark_as_read(self, message_id: str) -> bool:
        try:
            self.conn.select("INBOX")
            _, data = self.conn.search(None, f'HEADER Message-ID "<{message_id}>"')
            if data[0]:
                self.conn.store(data[0].split()[0], "+FLAGS", "\\Seen")
            return True
        except Exception:
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
