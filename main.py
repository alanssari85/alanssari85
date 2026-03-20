"""
Multi-Layer AI Agent — Interactive Demo
========================================
Run:
    python main.py              # Interactive chat
    python main.py --verbose    # Show all layer outputs
    python main.py --demo       # Run built-in demo queries
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def _get_console():
    if RICH_AVAILABLE:
        return Console()
    return None


console = _get_console()


def print_header():
    if RICH_AVAILABLE and console:
        title = Text("🧠 Multi-Layer AI Agent", style="bold cyan")
        subtitle = Text(
            "6-layer cognitive architecture: Perception → Memory → "
            "Reasoning → Planning → Execution → Reflection",
            style="dim"
        )
        console.print(Panel(f"{title}\n{subtitle}", border_style="cyan"))
    else:
        print("=" * 60)
        print("Multi-Layer AI Agent")
        print("6 Layers: Perception→Memory→Reasoning→Planning→Execution→Reflection")
        print("=" * 60)


def print_layer_info(response, verbose: bool = False):
    if not verbose:
        return
    if RICH_AVAILABLE and console:
        table = Table(title="Layer Analysis", show_header=True, header_style="bold magenta")
        table.add_column("Layer", style="cyan")
        table.add_column("Output", style="white")

        p = response.perception
        if p:
            table.add_row("1. Perception", f"Intent: {p.intent} | Complexity: {p.complexity} | Lang: {p.language}")

        r = response.reasoning
        if r:
            insights = "; ".join(r.key_insights[:2]) if r.key_insights else "—"
            table.add_row("3. Reasoning", f"Conf: {r.confidence:.1f} | {insights[:80]}")

        plan = response.plan
        if plan:
            table.add_row("4. Planning", f"Strategy: {plan.strategy} | Steps: {len(plan.steps)}")

        ref = response.reflection
        if ref:
            table.add_row(
                "6. Reflection",
                f"Quality: {ref.quality_score:.1f} | Completeness: {ref.completeness:.1f}"
            )

        console.print(table)
    else:
        print("\n--- Layer Analysis ---")
        if response.perception:
            p = response.perception
            print(f"Perception: intent={p.intent}, complexity={p.complexity}")
        if response.reasoning:
            r = response.reasoning
            print(f"Reasoning:  confidence={r.confidence:.1f}")
        if response.plan:
            print(f"Planning:   strategy={response.plan.strategy}, steps={len(response.plan.steps)}")
        if response.reflection:
            ref = response.reflection
            print(f"Reflection: quality={ref.quality_score:.1f}")
        print("--- End Analysis ---\n")


def print_response(response, verbose: bool = False):
    if verbose:
        print_layer_info(response, verbose)

    if RICH_AVAILABLE and console:
        console.print(
            Panel(
                response.final_answer,
                title=f"[bold green]Agent Response (Turn {response.turn})[/bold green]",
                border_style="green",
            )
        )
    else:
        print(f"\nAgent (Turn {response.turn}):")
        print("-" * 40)
        print(response.final_answer)
        print("-" * 40)


DEMO_QUERIES = [
    "What is 123 * 456?",
    "Write a short Python function that checks if a number is prime.",
    "ما هي عاصمة المملكة العربية السعودية؟",
    "Explain recursion with a simple example.",
]


def run_demo(agent, verbose: bool = False):
    print_header()
    if RICH_AVAILABLE and console:
        console.print("[yellow]Running demo queries...[/yellow]\n")
    else:
        print("Running demo queries...\n")

    for query in DEMO_QUERIES:
        if RICH_AVAILABLE and console:
            console.print(f"\n[bold blue]Query:[/bold blue] {query}")
        else:
            print(f"\nQuery: {query}")

        response = agent.chat(query)
        print_response(response, verbose)

    stats = agent.get_memory_stats()
    if RICH_AVAILABLE and console:
        console.print(f"\n[dim]Memory stats: {stats}[/dim]")
    else:
        print(f"\nMemory stats: {stats}")


def run_interactive(agent, verbose: bool = False):
    print_header()
    if RICH_AVAILABLE and console:
        console.print("[dim]Type your message and press Enter. Type 'exit' to quit, 'reset' to clear memory.[/dim]\n")
    else:
        print("Type your message and press Enter. Type 'exit' to quit, 'reset' to clear memory.\n")

    while True:
        try:
            if RICH_AVAILABLE and console:
                user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
            else:
                user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "خروج"):
            print("Goodbye! / وداعاً!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("Memory cleared.")
            continue
        if user_input.lower() == "tools":
            print(f"Available tools: {agent.list_tools()}")
            continue
        if user_input.lower() == "stats":
            print(f"Memory: {agent.get_memory_stats()}")
            continue

        try:
            response = agent.chat(user_input)
            print_response(response, verbose)
        except Exception as exc:
            if RICH_AVAILABLE and console:
                console.print(f"[red]Error: {exc}[/red]")
            else:
                print(f"Error: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Multi-Layer AI Agent")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all layer outputs")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo")
    parser.add_argument("--no-reflection", action="store_true", help="Disable reflection layer")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Import here to avoid errors if anthropic not installed
    from agent import MultiLayerAgent

    agent = MultiLayerAgent(
        verbose=args.verbose,
        enable_reflection=not args.no_reflection,
    )

    if args.demo:
        run_demo(agent, verbose=args.verbose)
    else:
        run_interactive(agent, verbose=args.verbose)


if __name__ == "__main__":
    main()
