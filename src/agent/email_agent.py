import json
from datetime import datetime
from typing import Optional

import anthropic
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import settings
from src.models.email import Email, EmailAnalysis, DailyBriefing, EmailCategory, Priority
from src.agent.prompts import SYSTEM_PROMPT, BATCH_ANALYSIS_PROMPT, BRIEFING_PROMPT
from src.agent.tools import EMAIL_ANALYSIS_TOOL, BRIEFING_TOOL
from src.storage import database as db

console = Console()


class EmailAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-6"

    def _format_emails_for_prompt(self, emails: list[Email]) -> str:
        formatted = []
        for email in emails:
            formatted.append({
                "id": email.id,
                "de": f"{email.sender} <{email.sender_email}>",
                "objet": email.subject,
                "date": email.date.strftime("%d/%m/%Y %H:%M"),
                "corps": email.body[:2000] if email.body else email.snippet,
            })
        return json.dumps(formatted, ensure_ascii=False, indent=2)

    def analyze_emails(self, emails: list[Email]) -> list[EmailAnalysis]:
        if not emails:
            return []

        analyses = []
        batch_size = 10

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Analyse de {len(emails)} emails en cours...", total=None
            )

            for i in range(0, len(emails), batch_size):
                batch = emails[i : i + batch_size]
                emails_json = self._format_emails_for_prompt(batch)

                messages = [
                    {
                        "role": "user",
                        "content": BATCH_ANALYSIS_PROMPT.format(emails_json=emails_json),
                    }
                ]

                email_map = {e.id: e for e in batch}
                analyzed_ids = set()

                while len(analyzed_ids) < len(batch):
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=8192,
                        system=SYSTEM_PROMPT,
                        tools=[EMAIL_ANALYSIS_TOOL],
                        messages=messages,
                    )

                    tool_calls = []
                    for block in response.content:
                        if block.type == "tool_use" and block.name == "analyze_email":
                            tool_calls.append(block)
                            data = block.input
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
                                    action_required=data.get("action_required", False),
                                    action_description=data.get("action_description"),
                                    deadline=data.get("deadline"),
                                    draft_reply=data.get("draft_reply"),
                                )
                                analyses.append(analysis)
                                db.save_analysis(analysis)
                                analyzed_ids.add(email_id)
                            except Exception as e:
                                console.print(f"[yellow]Erreur analyse {email_id}: {e}[/yellow]")

                    if response.stop_reason == "end_turn" or not tool_calls:
                        break

                    tool_results = [
                        {
                            "type": "tool_result",
                            "tool_use_id": tc.id,
                            "content": "Analyse enregistrée.",
                        }
                        for tc in tool_calls
                    ]
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

                progress.update(
                    task,
                    description=f"[cyan]{len(analyses)}/{len(emails)} emails analysés...",
                )

        console.print(f"[green]✓ {len(analyses)} emails analysés[/green]")
        return analyses

    def generate_briefing(self, emails: list[Email], analyses: list[EmailAnalysis]) -> DailyBriefing:
        urgent_count = sum(1 for a in analyses if a.category == EmailCategory.URGENT)
        important_count = sum(1 for a in analyses if a.category == EmailCategory.IMPORTANT)
        action_required_count = sum(1 for a in analyses if a.action_required)

        analyses_summary = []
        for analysis in sorted(analyses, key=lambda x: x.priority.value, reverse=True)[:20]:
            email = next((e for e in emails if e.id == analysis.email_id), None)
            if email:
                analyses_summary.append(
                    f"[{analysis.category.value.upper()}] {email.subject} (de: {email.sender}): {analysis.summary}"
                )

        with console.status("[cyan]Génération du briefing exécutif...[/cyan]"):
            messages = [
                {
                    "role": "user",
                    "content": BRIEFING_PROMPT.format(
                        count=len(emails),
                        analyses_summary="\n".join(analyses_summary),
                    ),
                }
            ]

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=[BRIEFING_TOOL],
                messages=messages,
            )

            briefing_data = {
                "executive_summary": "",
                "priority_list": [],
                "alerts": [],
            }

            for block in response.content:
                if block.type == "tool_use" and block.name == "generate_briefing":
                    briefing_data = block.input
                    break

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

    def run(self, emails: list[Email]) -> tuple[list[EmailAnalysis], Optional[DailyBriefing]]:
        if not emails:
            console.print("[yellow]Aucun email à analyser.[/yellow]")
            return [], None

        console.print(f"\n[bold blue]Stafy démarre l'analyse de {len(emails)} emails...[/bold blue]\n")

        for email in emails:
            db.save_email(email)

        analyses = self.analyze_emails(emails)
        briefing = self.generate_briefing(emails, analyses)

        return analyses, briefing
