"""
DealHunter AI — Main Agent Orchestrator
ينسّق جميع الطبقات السبع ويُخرج تقريراً شاملاً.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from deal_hunter.layers.sensing import run_sensing
from deal_hunter.layers.analysis import run_analysis
from deal_hunter.layers.scoring import run_scoring
from deal_hunter.layers.decision import run_decision
from deal_hunter.layers.planning import run_planning
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
    Multi-Layer AI Agent for profit opportunity discovery and execution.

    Architecture:
    1. Sensing      — Scan opportunity sources
    2. Analysis     — Deep dive into each opportunity
    3. Scoring      — Calculate opportunity score
    4. Decision     — Select best opportunities
    5. Planning     — Build execution roadmap
    6. Execution    — Generate ready-to-use artifacts
    7. Optimization — Learn and improve
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        categories: Optional[list[str]] = None,
        top_n: int = 3,
        execution_type: str = "offer",
    ):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.categories = categories or DEFAULT_CATEGORIES
        self.top_n = top_n
        self.execution_type = execution_type
        self.session_results: list[dict] = []

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def run(self) -> dict:
        """
        Execute the full multi-layer pipeline and return a structured report.
        """
        console.print(
            Panel.fit(
                "[bold cyan]🎯 DealHunter AI — Starting Opportunity Discovery Session[/bold cyan]\n"
                f"[dim]Categories: {len(self.categories)} | Top: {self.top_n} opportunities[/dim]",
                border_style="cyan",
            )
        )

        all_opportunities: list[dict] = []

        # ── Layer 1: Sensing ──────────────────
        console.rule("[bold blue]🔍 Layer 1 — Sensing[/bold blue]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for category in self.categories:
                task = progress.add_task(
                    f"Scanning: [cyan]{category}[/cyan]", total=None
                )
                opps = run_sensing(self.client, category)
                for opp in opps:
                    opp["category"] = category
                all_opportunities.extend(opps)
                progress.remove_task(task)

        console.print(
            f"[green]✓ Discovered {len(all_opportunities)} opportunities[/green]"
        )

        # ── Layer 2 & 3: Analysis + Scoring ──
        console.rule("[bold blue]📊 Layers 2–3 — Analysis & Scoring[/bold blue]")
        scored: list[dict] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for opp in all_opportunities:
                task = progress.add_task(
                    f"Analyzing: [yellow]{opp.get('name', '...')}[/yellow]",
                    total=None,
                )
                analysed = run_analysis(self.client, opp)
                scored_opp = run_scoring(self.client, analysed)
                scored.append(scored_opp)
                progress.remove_task(task)

        # ── Layer 4: Decision ─────────────────
        console.rule("[bold blue]🧠 Layer 4 — Decision[/bold blue]")
        decided = run_decision(scored)
        selected = [o for o in decided if o.get("selected")]

        self._print_scoring_table(decided[:10])  # Show top 10

        console.print(
            f"\n[green]✓ Selected {len(selected)} opportunities out of {len(decided)}[/green]"
        )

        # Limit to top N
        top_opportunities = selected[: self.top_n]

        # ── Layer 5 & 6: Planning + Execution ─
        console.rule("[bold blue]📋 Layers 5–6 — Planning & Execution[/bold blue]")
        final_opportunities: list[dict] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for opp in top_opportunities:
                task = progress.add_task(
                    f"Planning: [magenta]{opp.get('name', '...')}[/magenta]",
                    total=None,
                )
                planned = run_planning(self.client, opp)
                executed = run_execution(
                    self.client, planned, self.execution_type
                )
                final_opportunities.append(executed)
                progress.remove_task(task)

        self.session_results = final_opportunities

        # ── Layer 7: Optimization ─────────────
        console.rule("[bold blue]⚡ Layer 7 — Optimization[/bold blue]")
        optimization_report = run_optimization(self.client, decided)

        # ── Build final report ────────────────
        report = self._build_report(final_opportunities, optimization_report)
        self._print_final_report(report)

        return report

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────

    def _build_report(
        self,
        opportunities: list[dict],
        optimization: dict,
    ) -> dict:
        """Assemble the final structured JSON report."""
        results = []
        for opp in opportunities:
            scores = opp.get("scores", {})
            analysis = opp.get("analysis", {})
            plan = opp.get("plan", {})
            execution = opp.get("execution", {})

            results.append({
                "opportunity": opp.get("name", "N/A"),
                "source": opp.get("source", "N/A"),
                "analysis": {
                    "demand": analysis.get("demand_level", "N/A"),
                    "competition": analysis.get("competition_level", "N/A"),
                    "estimated_revenue": analysis.get("estimated_revenue_usd", {}),
                    "time_to_revenue": f"{analysis.get('time_to_first_revenue_days', '?')} days",
                },
                "scores": {
                    "profitability": scores.get("profitability", {}).get("score", 0),
                    "ease": scores.get("ease", {}).get("score", 0),
                    "scalability": scores.get("scalability", {}).get("score", 0),
                    "risk": scores.get("risk", {}).get("score", 0),
                    "final_score": scores.get("final_score", 0),
                },
                "decision": opp.get("decision", "N/A"),
                "execution_plan": [
                    f"Step {s.get('step', i+1)}: {s.get('action', '')}"
                    for i, s in enumerate(
                        plan.get("execution_steps", [])[:6]
                    )
                ],
                "profit_mechanism": plan.get("profit_mechanism", "N/A"),
                "generated_content": execution.get("content", "")[:500] + "...",
                "confidence": f"{min(100, int(scores.get('final_score', 0) * 4))}%",
            })

        return {
            "DealHunter_AI_Session": {
                "selected_opportunities": results,
                "optimization_report": optimization,
            }
        }

    def _print_scoring_table(self, opportunities: list[dict]) -> None:
        """Print a rich table of scored opportunities."""
        table = Table(
            title="🏆 Scoring Table",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Opportunity", style="white", min_width=25)
        table.add_column("Profitability", justify="center")
        table.add_column("Ease", justify="center")
        table.add_column("Scalability", justify="center")
        table.add_column("Risk", justify="center")
        table.add_column("Score", justify="center", style="bold")
        table.add_column("Decision", style="dim")

        for opp in opportunities:
            scores = opp.get("scores", {})
            final = scores.get("final_score", 0)
            selected = opp.get("selected", False)

            score_color = (
                "green" if final >= 20
                else "yellow" if final >= 15
                else "red"
            )

            table.add_row(
                opp.get("name", "N/A")[:30],
                str(scores.get("profitability", {}).get("score", 0)),
                str(scores.get("ease", {}).get("score", 0)),
                str(scores.get("scalability", {}).get("score", 0)),
                str(scores.get("risk", {}).get("score", 0)),
                f"[{score_color}]{final}[/{score_color}]",
                "✅" if selected else "❌",
            )

        console.print(table)

    def _print_final_report(self, report: dict) -> None:
        """Print a summary of the final report."""
        console.print("\n")
        console.print(
            Panel.fit(
                "[bold green]✅ DealHunter AI Session Complete[/bold green]",
                border_style="green",
            )
        )

        session = report.get("DealHunter_AI_Session", {})
        opportunities = session.get("selected_opportunities", [])
        optimization = session.get("optimization_report", {})

        for i, opp in enumerate(opportunities, 1):
            score = opp.get("scores", {}).get("final_score", 0)
            confidence = opp.get("confidence", "0%")
            console.print(
                f"[bold cyan]{i}.[/bold cyan] [white]{opp.get('opportunity', '')}[/white] "
                f"| Score: [yellow]{score}[/yellow] "
                f"| Confidence: [green]{confidence}[/green]"
            )
            console.print(
                f"   [dim]Profit mechanism: {str(opp.get('profit_mechanism', ''))[:80]}[/dim]"
            )

        top = optimization.get("top_opportunity", "—")
        potential = optimization.get("estimated_monthly_potential_usd", 0)
        console.print(
            f"\n[bold]Best opportunity:[/bold] [cyan]{top}[/cyan]"
            f" | [bold]Monthly potential:[/bold] [green]${potential:,.0f}[/green]"
        )
