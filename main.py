#!/usr/bin/env python3
"""
DealHunter AI — Entry Point

Usage:
    python main.py
    python main.py --categories "AI Services" "Dropshipping"
    python main.py --top 5 --output offer
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from deal_hunter.agent import DealHunterAgent, DEFAULT_CATEGORIES


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="DealHunter AI — Profit Opportunity Discovery Agent"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Opportunity categories to search (space-separated)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of top opportunities to plan and execute (default: 3)",
    )
    parser.add_argument(
        "--output",
        choices=["offer", "pitch", "listing", "landing"],
        default="offer",
        help="Type of content generated in the execution layer",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        default="deal_hunter_report.json",
        help="Save the final report as JSON",
    )

    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "❌ Error: ANTHROPIC_API_KEY not found.\n"
            "Add your key to a .env file or set it as an environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    agent = DealHunterAgent(
        api_key=api_key,
        categories=args.categories or DEFAULT_CATEGORIES,
        top_n=args.top,
        execution_type=args.output,
    )

    report = agent.run()

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Report saved to: {args.save}")


if __name__ == "__main__":
    main()
