"""
Layer 1 — Opportunity Sensing Layer
مسح مصادر الفرص واستخراج الفرص ذات الطلب الحقيقي.
"""

import anthropic
import json


SENSING_SYSTEM = """أنت محلل فرص ربح محترف اسمك DealHunter AI.
مهمتك: مسح المصادر الرقمية واستخراج فرص ربح حقيقية وقابلة للتنفيذ.

ركز على:
- منصات العمل الحر (Freelance): Upwork, Fiverr, Toptal
- الأسواق الإلكترونية (Marketplaces): Amazon, eBay, Etsy, Gumroad
- أفكار SaaS وأدوات AI
- فرص Arbitrage (شراء رخيص وبيع بسعر أعلى)
- خدمات تسويق وإنشاء محتوى
- استشارات وخدمات B2B

استخرج 5 فرص على الأقل لكل فئة تُطلب منك.
كن محدداً: اذكر المنصة، نوع الخدمة، الجمهور المستهدف.
"""


def run_sensing(client: anthropic.Anthropic, category: str) -> list[dict]:
    """
    Scan opportunity sources for a given category.
    Returns a list of raw opportunity dicts.
    """
    prompt = f"""
امسح فرص الربح في فئة: **{category}**

لكل فرصة تجدها، أعد JSON بهذا الشكل:
{{
  "name": "اسم الفرصة",
  "source": "المصدر / المنصة",
  "description": "وصف مختصر",
  "target_audience": "الجمهور المستهدف",
  "estimated_monthly_demand": "مرتفع/متوسط/منخفض",
  "keywords": ["كلمة1", "كلمة2"]
}}

أعد قائمة JSON فقط بدون أي نص إضافي. مثال:
[{{"name": "...", "source": "...", ...}}, ...]
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SENSING_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "[]"
    )

    # Extract JSON array from response
    start = text.find("[")
    end = text.rfind("]") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return []
