"""
Layer 7 — Optimization Layer
تعلم من النتائج وتحسين الاستراتيجية.
"""

import anthropic
import json


OPTIMIZATION_SYSTEM = """أنت محلل أداء ومحسّن استراتيجي.
درّس النتائج واستخرج دروساً قابلة للتطبيق.
ركز على ما يمكن تحسينه في الجولة القادمة.
"""


def run_optimization(
    client: anthropic.Anthropic,
    session_results: list[dict],
) -> dict:
    """
    Analyze session results and generate optimization insights.

    session_results: list of processed opportunities with all layers data.
    Returns optimization report with lessons and next-cycle recommendations.
    """
    # Summarize results for analysis
    summary = []
    for opp in session_results:
        scores = opp.get("scores", {})
        summary.append({
            "name": opp.get("name", "غير محدد"),
            "category": opp.get("source", "غير محدد"),
            "final_score": scores.get("final_score", 0),
            "selected": opp.get("selected", False),
            "verdict": scores.get("verdict", "غير محدد"),
            "profitability": scores.get("profitability", {}).get("score", 0),
            "ease": scores.get("ease", {}).get("score", 0),
            "scalability": scores.get("scalability", {}).get("score", 0),
            "risk": scores.get("risk", {}).get("score", 0),
        })

    prompt = f"""
حلّل نتائج جلسة البحث عن الفرص هذه وأعد تقرير تحسين:

النتائج:
{json.dumps(summary, ensure_ascii=False, indent=2)}

أعد تقرير JSON:
{{
  "top_opportunity": "اسم أفضل فرصة",
  "top_category": "أفضل فئة/مجال",
  "patterns_found": ["نمط1", "نمط2"],
  "avoided_mistakes": ["خطأ تجنبناه1", "خطأ2"],
  "next_cycle_focus": ["توجيه1", "توجيه2"],
  "scoring_calibration": "هل نحتاج تعديل معايير التقييم؟",
  "recommended_categories_next": ["فئة1", "فئة2"],
  "confidence_level": "عالي/متوسط/منخفض",
  "estimated_monthly_potential_usd": 0,
  "action_items": [
    {{"priority": "عالي", "action": "الإجراء", "deadline": "الموعد"}}
  ]
}}

أعد JSON فقط.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=OPTIMIZATION_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    report = {}
    if start != -1 and end > start:
        try:
            report = json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return report
