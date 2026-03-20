"""
Layer 5 — Strategic Planning Layer
إنشاء خطة تنفيذ واضحة لكل فرصة مختارة.
"""

import anthropic
import json


PLANNING_SYSTEM = """أنت خبير استراتيجي في تنفيذ مشاريع الربح الرقمي.
ضع خططاً واقعية وقابلة للتنفيذ الفوري.
ركز على السرعة والعائد السريع. تجنب التعقيد غير الضروري.
"""


def run_planning(client: anthropic.Anthropic, opportunity: dict) -> dict:
    """
    Create a detailed execution plan for a selected opportunity.
    """
    analysis = opportunity.get("analysis", {})
    scores = opportunity.get("scores", {})

    prompt = f"""
ضع خطة تنفيذ تفصيلية لهذه الفرصة:

الفرصة: {opportunity.get('name', 'غير محدد')}
المصدر: {opportunity.get('source', 'غير محدد')}
الزاوية المميزة: {analysis.get('unique_angle', 'غير محدد')}
توظيف الذكاء الاصطناعي: {analysis.get('ai_leverage', 'غير محدد')}
المهارات المطلوبة: {analysis.get('required_skills', [])}
الأدوات المطلوبة: {analysis.get('required_tools', [])}
الدرجة النهائية: {scores.get('final_score', 0)}

أعد خطة JSON شاملة:
{{
  "profit_mechanism": "كيف سنجني المال بالتحديد",
  "execution_steps": [
    {{"step": 1, "action": "الإجراء", "duration": "المدة", "tools": ["أداة"], "output": "النتيجة"}},
    {{"step": 2, "action": "الإجراء", "duration": "المدة", "tools": ["أداة"], "output": "النتيجة"}}
  ],
  "week_1_goals": ["هدف1", "هدف2"],
  "month_1_revenue_target_usd": 0,
  "pricing_strategy": "استراتيجية التسعير",
  "acquisition_channels": ["قناة1", "قناة2"],
  "ai_automation_plan": "كيف نوظف الذكاء الاصطناعي",
  "outsourcing_plan": "ما يمكن تفويضه",
  "scaling_roadmap": "مسار التوسع",
  "first_client_strategy": "استراتيجية الحصول على أول عميل"
}}

أعد JSON فقط.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        thinking={"type": "adaptive"},
        system=PLANNING_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    plan = {}
    if start != -1 and end > start:
        try:
            plan = json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return {**opportunity, "plan": plan}
