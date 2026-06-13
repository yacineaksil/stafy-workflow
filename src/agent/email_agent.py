import json
import logging
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.llm import get_llm_client
from src.llm.base import LLMClient
from src.models.email import Email, EmailAnalysis, DailyBriefing, EmailCategory, Priority
from src.agent.prompts import SYSTEM_PROMPT, BATCH_ANALYSIS_PROMPT, BRIEFING_PROMPT
from src.agent.tools import EMAIL_ANALYSIS_TOOL, BRIEFING_TOOL
from src.storage import database as db

log = logging.getLogger(__name__)
console = Console(stderr=True)

BATCH_SIZE = 5
MAX_TOOL_ROUNDS = 3


class EmailAgent:
    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or get_llm_client()
        console.print(f"[dim]LLM : {self.llm.name}[/dim]")

    # ── Analyse emails ────────────────────────────────────────────────────────

    def analyze_emails(self, emails: list[Email]) -> list[EmailAnalysis]:
        if not emails:
            return []

        analyses: list[EmailAnalysis] = []

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
            task = prog.add_task(f"[cyan]Analyse de {len(emails)} emails…", total=None)

            for i in range(0, len(emails), BATCH_SIZE):
                batch = emails[i : i + BATCH_SIZE]
                batch_analyses = self._analyze_batch(batch)
                analyses.extend(batch_analyses)
                prog.update(task, description=f"[cyan]{len(analyses)}/{len(emails)} analysés…")

        console.print(f"[green]✓ {len(analyses)} emails analysés[/green]")
        return analyses

    def _analyze_batch(self, batch: list[Email]) -> list[EmailAnalysis]:
        emails_json = json.dumps(
            [
                {
                    "id": e.id,
                    "de": f"{e.sender} <{e.sender_email}>",
                    "objet": e.subject,
                    "date": e.date.strftime("%d/%m/%Y %H:%M"),
                    "corps": (e.body or e.snippet)[:2000],
                }
                for e in batch
            ],
            ensure_ascii=False,
            indent=2,
        )

        email_map = {e.id: e for e in batch}
        analyses: list[EmailAnalysis] = []
        messages = [{"role": "user", "content": BATCH_ANALYSIS_PROMPT.format(emails_json=emails_json)}]

        for _round in range(MAX_TOOL_ROUNDS):
            stop_reason, tool_calls, content_blocks = self.llm.chat_with_tools(
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=[EMAIL_ANALYSIS_TOOL],
                max_tokens=8192,
            )

            new_analyses = []
            for call in tool_calls:
                if call["name"] != "analyze_email":
                    continue
                data = call["input"]
                email_id = data.get("email_id", "")
                if email_id not in email_map:
                    continue
                try:
                    analysis = EmailAnalysis(
                        email_id=email_id,
                        category=EmailCategory(data["category"]),
                        priority=Priority(data["priority"]),
                        sentiment=data.get("sentiment", "neutre"),
                        summary=data.get("summary", ""),
                        key_points=data.get("key_points", []),
                        action_required=bool(data.get("action_required", False)),
                        action_description=data.get("action_description"),
                        deadline=data.get("deadline"),
                        draft_reply=data.get("draft_reply"),
                    )
                    new_analyses.append(analysis)
                    db.save_analysis(analysis)
                except Exception as e:
                    log.warning("Erreur analyse %s : %s", email_id, e)

            analyses.extend(new_analyses)

            if stop_reason == "end_turn" or not tool_calls:
                break

            # Continuer le loop tool_use pour les providers qui le supportent
            tool_results = [
                {"type": "tool_result", "tool_use_id": c["id"], "content": "Enregistré."}
                for c in tool_calls
            ]
            messages.append({"role": "assistant", "content": content_blocks or []})
            messages.append({"role": "user", "content": tool_results})

        return analyses

    # ── Briefing ──────────────────────────────────────────────────────────────

    def generate_briefing(self, emails: list[Email], analyses: list[EmailAnalysis]) -> DailyBriefing:
        urgent_count = sum(1 for a in analyses if a.category == EmailCategory.URGENT)
        important_count = sum(1 for a in analyses if a.category == EmailCategory.IMPORTANT)
        action_required_count = sum(1 for a in analyses if a.action_required)

        top = sorted(analyses, key=lambda x: x.priority.value, reverse=True)[:20]
        summary_lines = []
        for a in top:
            e = next((x for x in emails if x.id == a.email_id), None)
            if e:
                summary_lines.append(
                    f"[{a.category.value.upper()}] {e.subject} (de: {e.sender}): {a.summary}"
                )

        with console.status("[cyan]Génération du briefing…[/cyan]"):
            _, tool_calls, _ = self.llm.chat_with_tools(
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": BRIEFING_PROMPT.format(
                        count=len(emails),
                        analyses_summary="\n".join(summary_lines),
                    ),
                }],
                tools=[BRIEFING_TOOL],
                max_tokens=2048,
            )

        briefing_data = next(
            (c["input"] for c in tool_calls if c["name"] == "generate_briefing"),
            {"executive_summary": "", "priority_list": [], "alerts": []},
        )

        briefing = DailyBriefing(
            total_emails=len(emails),
            urgent_count=urgent_count,
            important_count=important_count,
            action_required_count=action_required_count,
            executive_summary=briefing_data.get("executive_summary", ""),
            priority_list=briefing_data.get("priority_list", []),
            alerts=briefing_data.get("alerts", []),
        )
        db.save_briefing(briefing)
        console.print("[green]✓ Briefing généré[/green]")
        return briefing

    # ── Point d'entrée ────────────────────────────────────────────────────────

    def run(self, emails: list[Email]) -> tuple[list[EmailAnalysis], Optional[DailyBriefing]]:
        if not emails:
            console.print("[yellow]Aucun email à analyser.[/yellow]")
            return [], None

        console.print(f"\n[bold blue]Stafy – analyse de {len(emails)} emails ({self.llm.name})[/bold blue]\n")

        for e in emails:
            db.save_email(e)

        analyses = self.analyze_emails(emails)
        briefing = self.generate_briefing(emails, analyses)
        return analyses, briefing
