from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EmailCategory(str, Enum):
    URGENT = "urgent"
    IMPORTANT = "important"
    NORMAL = "normal"
    NEWSLETTER = "newsletter"
    SPAM = "spam"


class Priority(int, Enum):
    CRITIQUE = 5
    HAUTE = 4
    MOYENNE = 3
    BASSE = 2
    NEGLIGEABLE = 1


class Email(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    recipient: str
    date: datetime
    body: str
    snippet: str
    is_read: bool = False
    labels: list[str] = Field(default_factory=list)


class EmailAnalysis(BaseModel):
    email_id: str
    category: EmailCategory
    priority: Priority
    sentiment: str
    summary: str
    key_points: list[str]
    action_required: bool
    action_description: Optional[str] = None
    deadline: Optional[str] = None
    draft_reply: Optional[str] = None
    analyzed_at: datetime = Field(default_factory=datetime.now)


class DailyBriefing(BaseModel):
    date: datetime = Field(default_factory=datetime.now)
    total_emails: int
    urgent_count: int
    important_count: int
    action_required_count: int
    executive_summary: str
    priority_list: list[str]
    alerts: list[str]
    completed_tasks: list[str] = Field(default_factory=list)


class DashboardStats(BaseModel):
    total_unread: int
    urgent: int
    important: int
    with_drafts: int
    processed_today: int
