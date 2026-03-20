"""
DealHunter AI — Main Orchestrator

Three-mode pipeline:
  🔍 Hunter Mode   → scan for fast-money opportunities (1–7 days)
  📊 Evaluator Mode → score each on 5 criteria (0–10 each, max 50)
  💰 Closer Mode   → convert the ONE winner into a ready-to-sell offer

Plus:
  ⚡ Optimization  → lessons for the next session
"""

from __future__ import annotations

import json
import os
from typing import Optional

import anthropic
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from deal_hunter.layers.sensing import run_sensing
from deal_hunter.layers.scoring import run_scoring
from deal_hunter.layers.decision import run_decision
from deal_hunter.layers.execution import run_execution
from deal_hunter.layers.optimization import run_optimization

console = Console()

DEFAULT_CATEGORIES = [
    "AI Services and Content Automation",
    "Web and App Development for Small Businesses",
    "Digital Marketing and Social Media Management",
    "Dropshipping and Amazon FBA",
    "B2B Consulting and Coaching",
]


class DealHunterAgent:
    """
    Revenue-focused decision engine.

    Goal: find ONE high-probability money-making opportunity and convert it
    into a ready-to-sell offer — within a single session.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        categories: Optional[list[str]] = None,
    ):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.categories = categories or DEFAULT_CATEGORIES

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def run(self) -> dict:
        """Execute the full 3-mode pipeline and return the final report."""
        console.print(
            Panel.fit(
                "[bold cyan]🎯 DealHunter AI — Revenue Discovery Session[/bold cyan]\n"
                "[dim]Hunter → Evaluator → Closer[/dim]",
                border_style="cyan",
            )
        )

        # ── 🔍 Hunter Mode ─────────────────────────────────────
        console.rule("[bold blue]🔍 HUNTER MODE — Scanning for Opportunities[/bold blue]")
        all_valid: list[dict] = []
        all_rejected: list[dict] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for category in self.categories:
                task = progress.add_task(
                    f"Hunting: [cyan]{category}[/cyan]", total=None
                )
                valid, rejected = run_sensing(self.client, category)
                all_valid.extend(valid)
                all_rejected.extend(rejected)
                progress.remove_task(task)

        console.print(
            f"[green]✓ Found {len(all_valid)} valid opportunities[/green] "
            f"[dim]({len(all_rejected)} rejected by Hunter)[/dim]"
        )

        if not all_valid:
            console.print("[red]✗ No valid opportunities found. Exiting.[/red]")
            return {"error": "No valid opportunities discovered."}

        # ── 📊 Evaluator Mode ──────────────────────────────────
        console.rule("[bold blue]📊 EVALUATOR MODE — Scoring Opportunities[/bold blue]")
        scored: list[dict] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for opp in all_valid:
                task = progress.add_task(
                    f"Evaluating: [yellow]{opp.get('name', '...')}[/yellow]",
                    total=None,
                )
                scored_opp = run_scoring(self.client, opp)
                scored.append(scored_opp)
                progress.remove_task(task)

        self._print_scores_table(scored)

        # ── Decision: Pick ONE winner ──────────────────────────
        decision = run_decision(scored)
        winner_raw = decision["winner"]

        if not winner_raw:
            console.print("[red]✗ Could not select a winner.[/red]")
            return {"error": "Decision engine found no winner."}

        console.print(
            f"\n[bold green]🏆 Winner:[/bold green] [white]{winner_raw.get('name')}[/white] "
            f"| Score: [yellow]{winner_raw.get('scores', {}).get('final_score', 0)}/50[/yellow]"
        )
        console.print(f"[dim]{decision['selection_note']}[/dim]")

        # ── 💰 Closer Mode ─────────────────────────────────────
        console.rule("[bold blue]💰 CLOSER MODE — Building Sellable Offer[/bold blue]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Closing: [magenta]{winner_raw.get('name')}[/magenta]",
                total=None,
            )
            winner_with_offer = run_execution(self.client, winner_raw)
            progress.remove_task(task)

        offer = winner_with_offer.get("offer", {})
        self._print_offer(offer)

        # ── ⚡ Optimization ────────────────────────────────────
        console.rule("[bold blue]⚡ OPTIMIZATION — Lessons for Next Session[/bold blue]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing session...", total=None)
            opt_report = run_optimization(
                self.client,
                all_scored=scored,
                winner=winner_raw,
                rejected_log=all_rejected,
            )
            progress.remove_task(task)

        if opt_report.get("next_session_focus"):
            console.print("[bold]Next session focus:[/bold]")
            for tip in opt_report["next_session_focus"]:
                console.print(f"  [dim]→[/dim] {tip}")

        # ── Build final report ─────────────────────────────────
        report = {
            "DealHunter_AI": {
                "offer": offer,
                "winner_scores": winner_raw.get("scores", {}),
                "selection_note": decision["selection_note"],
                "runner_ups": [
                    {
                        "name": o.get("name"),
                        "score": o.get("scores", {}).get("final_score", 0),
                    }
                    for o in decision["runner_ups"][:5]
                ],
                "rejected_by_hunter": [
                    {
                        "name": o.get("name"),
                        "reason": o.get("rejection_reason"),
                    }
                    for o in all_rejected
                ],
                "optimization": opt_report,
            }
        }

        console.print(
            Panel.fit(
                "[bold green]✅ Session Complete — Your offer is ready to execute.[/bold green]",
                border_style="green",
            )
        )

        return report

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────

    def _print_scores_table(self, opportunities: list[dict]) -> None:
        table = Table(
            title="📊 Evaluator Scores (max 50)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Opportunity", style="white", min_width=28)
        table.add_column("Profit", justify="center")
        table.add_column("Ease", justify="center")
        table.add_column("Speed", justify="center")
        table.add_column("Competition", justify="center")
        table.add_column("Risk", justify="center")
        table.add_column("Total", justify="center", style="bold")

        ranked = sorted(
            opportunities,
            key=lambda x: x.get("scores", {}).get("final_score", 0),
            reverse=True,
        )

        for opp in ranked[:10]:
            s = opp.get("scores", {})
            final = s.get("final_score", 0)
            color = "green" if final >= 35 else "yellow" if final >= 25 else "red"
            table.add_row(
                opp.get("name", "N/A")[:30],
                str(s.get("profit_potential", {}).get("score", 0)),
                str(s.get("ease_of_execution", {}).get("score", 0)),
                str(s.get("speed_to_first_payment", {}).get("score", 0)),
                str(s.get("competition_level", {}).get("score", 0)),
                str(s.get("risk_level", {}).get("score", 0)),
                f"[{color}]{final}[/{color}]",
            )

        console.print(table)

    def _print_offer(self, offer: dict) -> None:
        if not offer or offer.get("parse_error"):
            console.print("[red]Could not parse offer JSON.[/red]")
            return

        console.print(
            Panel(
                f"[bold white]{offer.get('opportunity', 'N/A')}[/bold white]\n\n"
                f"[cyan]Target:[/cyan] {offer.get('target_customer', 'N/A')}\n"
                f"[cyan]Pain:[/cyan] {offer.get('pain_point', 'N/A')}\n"
                f"[cyan]Solution:[/cyan] {offer.get('solution', 'N/A')}\n"
                f"[cyan]Value Prop:[/cyan] {offer.get('value_proposition', 'N/A')}\n"
                f"[cyan]Pricing:[/cyan] {offer.get('pricing_model', 'N/A')}\n"
                f"[cyan]7-Day Earnings:[/cyan] [green]{offer.get('expected_earnings_7_days', 'N/A')}[/green]\n"
                f"[cyan]Confidence:[/cyan] [yellow]{offer.get('confidence', 'N/A')}[/yellow]",
                title="💰 THE OFFER",
                border_style="green",
            )
        )

        plan = offer.get("execution_plan", [])
        if plan:
            console.print("[bold]Execution Plan:[/bold]")
            for step in plan:
                console.print(f"  [dim]▸[/dim] {step}")

        sales_msg = offer.get("sales_message", "")
        if sales_msg:
            console.print(
                Panel(
                    sales_msg,
                    title="📩 Sales Message (copy-paste ready)",
                    border_style="blue",
                )
            )
