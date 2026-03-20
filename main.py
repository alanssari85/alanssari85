#!/usr/bin/env python3
"""
DealHunter AI — Entry Point
نقطة الدخول الرئيسية للوكيل.

الاستخدام:
    python main.py
    python main.py --categories "خدمات AI" "Dropshipping"
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
        description="DealHunter AI — وكيل البحث عن فرص الربح"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="فئات الفرص المراد البحث عنها (مسافة تفصل بينها)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="عدد الفرص المختارة للتخطيط والتنفيذ (افتراضي: 3)",
    )
    parser.add_argument(
        "--output",
        choices=["offer", "pitch", "listing", "landing"],
        default="offer",
        help="نوع المحتوى المُنشأ في طبقة التنفيذ",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        default="deal_hunter_report.json",
        help="حفظ التقرير النهائي بتنسيق JSON",
    )

    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "❌ خطأ: لم يتم العثور على ANTHROPIC_API_KEY\n"
            "أضف مفتاحك في ملف .env أو كمتغير بيئة.",
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
        print(f"\n💾 تم حفظ التقرير في: {args.save}")


if __name__ == "__main__":
    main()
