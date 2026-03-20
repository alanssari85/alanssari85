"""
Layer 2 — Deep Analysis Layer
تحليل عميق لكل فرصة: الطلب، المنافسة، الربح، السرعة.
"""

import anthropic
import json


ANALYSIS_SYSTEM = """أنت محلل أعمال رقمية متخصص في تقييم فرص الربح عبر الإنترنت.
قيّم كل فرصة بموضوعية ودقة بناءً على بيانات السوق الحقيقية.
لا تبالغ في التفاؤل — كن واقعياً.
"""


def run_analysis(client: anthropic.Anthropic, opportunity: dict) -> dict:
    """
    Deep analysis of a single opportunity.
    Returns enriched opportunity dict with analysis fields.
    """
    prompt = f"""
حلّل هذه الفرصة بعمق:

الفرصة: {opportunity.get('name', 'غير محدد')}
المصدر: {opportunity.get('source', 'غير محدد')}
الوصف: {opportunity.get('description', 'غير محدد')}
الجمهور: {opportunity.get('target_audience', 'غير محدد')}

أعد تحليلاً شاملاً بتنسيق JSON:
{{
  "demand_level": "مرتفع/متوسط/منخفض",
  "demand_explanation": "سبب مستوى الطلب",
  "competition_level": "مرتفع/متوسط/منخفض",
  "competition_explanation": "طبيعة المنافسة",
  "estimated_revenue_usd": {{"min": 0, "max": 0, "currency": "USD", "period": "شهري"}},
  "time_to_first_revenue_days": 0,
  "automation_potential": "مرتفع/متوسط/منخفض",
  "required_skills": ["مهارة1", "مهارة2"],
  "required_tools": ["أداة1", "أداة2"],
  "barriers_to_entry": "وصف الحواجز",
  "unique_angle": "الزاوية المميزة للدخول",
  "ai_leverage": "كيف يمكن توظيف الذكاء الاصطناعي"
}}

أعد JSON فقط.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=ANALYSIS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    analysis = {}
    if start != -1 and end > start:
        try:
            analysis = json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return {**opportunity, "analysis": analysis}
