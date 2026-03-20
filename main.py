#!/usr/bin/env python3
"""
DealHunter AI — Entry Point

Usage:
    python main.py
    python main.py --categories "AI Services" "B2B Consulting"
    python main.py --save my_report.json
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
        description="DealHunter AI — Find ONE opportunity and close it."
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Opportunity categories to hunt (space-separated)",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        default="deal_hunter_report.json",
        help="Save the final report as JSON (default: deal_hunter_report.json)",
    )

    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "❌ ANTHROPIC_API_KEY not found.\n"
            "Add it to a .env file or set it as an environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    agent = DealHunterAgent(
        api_key=api_key,
        categories=args.categories or DEFAULT_CATEGORIES,
    )

    report = agent.run()

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Full report saved to: {args.save}")


if __name__ == "__main__":
    main()
