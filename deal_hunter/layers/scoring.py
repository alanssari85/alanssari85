"""
Layer 3 — Scoring Engine
حساب درجة لكل فرصة: الربحية، السهولة، التوسع، المخاطر.
Opportunity Score = (الربحية + السهولة + التوسع) - المخاطر
"""

import anthropic
import json


SCORING_SYSTEM = """أنت محرك تقييم كمي للفرص التجارية.
أعط درجات من 0 إلى 10 لكل معيار بناءً على التحليل المقدم.
كن دقيقاً وقابلاً للمقارنة عبر الفرص المختلفة.
"""


def run_scoring(client: anthropic.Anthropic, opportunity: dict) -> dict:
    """
    Score an opportunity on profitability, ease, scalability, and risk.
    Returns opportunity dict with scores and final score.
    """
    analysis = opportunity.get("analysis", {})

    prompt = f"""
قيّم هذه الفرصة وأعطها درجات:

الفرصة: {opportunity.get('name', 'غير محدد')}
الطلب: {analysis.get('demand_level', 'غير محدد')}
المنافسة: {analysis.get('competition_level', 'غير محدد')}
الإيراد المتوقع: {analysis.get('estimated_revenue_usd', {})}
الوقت للدخل الأول: {analysis.get('time_to_first_revenue_days', 'غير محدد')} يوم
إمكانية الأتمتة: {analysis.get('automation_potential', 'غير محدد')}
الحواجز: {analysis.get('barriers_to_entry', 'غير محدد')}

أعد JSON بالدرجات (0-10 لكل معيار):
{{
  "profitability": {{
    "score": 0,
    "reason": "سبب الدرجة"
  }},
  "ease": {{
    "score": 0,
    "reason": "سبب الدرجة"
  }},
  "scalability": {{
    "score": 0,
    "reason": "سبب الدرجة"
  }},
  "risk": {{
    "score": 0,
    "reason": "سبب المخاطرة"
  }},
  "final_score": 0,
  "verdict": "ممتاز/جيد/متوسط/ضعيف"
}}

احسب: final_score = (profitability + ease + scalability) - risk
أعد JSON فقط.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SCORING_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    scores = {}
    if start != -1 and end > start:
        try:
            scores = json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # Recalculate final_score to ensure correctness
    p = scores.get("profitability", {}).get("score", 0)
    e = scores.get("ease", {}).get("score", 0)
    s = scores.get("scalability", {}).get("score", 0)
    r = scores.get("risk", {}).get("score", 0)
    scores["final_score"] = round((p + e + s) - r, 1)

    return {**opportunity, "scores": scores}
