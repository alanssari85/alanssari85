"""
Layer 6 — Execution Layer
محاكاة التنفيذ: كتابة عرض، رسالة تسويقية، أو وصف خدمة.
"""

import anthropic


EXECUTION_SYSTEM = """أنت copywriter ومسوّق رقمي محترف.
اكتب محتوى مقنعاً وفعالاً يحول القراء إلى عملاء.
استخدم أسلوباً واضحاً ومباشراً. ركز على القيمة والنتائج.
"""


def run_execution(
    client: anthropic.Anthropic,
    opportunity: dict,
    output_type: str = "offer",
) -> dict:
    """
    Generate execution artifacts for the opportunity.

    output_type options:
    - "offer"       : Service offer / proposal
    - "pitch"       : Cold outreach message
    - "listing"     : Marketplace listing description
    - "landing"     : Landing page copy
    """
    plan = opportunity.get("plan", {})
    analysis = opportunity.get("analysis", {})

    type_instructions = {
        "offer": "اكتب عرض خدمة احترافي (Service Proposal) يمكن إرساله للعملاء المحتملين",
        "pitch": "اكتب رسالة تواصل بارد (Cold Outreach) قصيرة ومقنعة لجذب أول عميل",
        "listing": "اكتب وصف خدمة لمنصة فايفر أو أبورك يجذب العملاء ويحقق مبيعات",
        "landing": "اكتب نص صفحة هبوط (Landing Page) مقنع لهذه الخدمة",
    }

    instruction = type_instructions.get(output_type, type_instructions["offer"])

    prompt = f"""
{instruction}

الفرصة: {opportunity.get('name', 'غير محدد')}
آلية الربح: {plan.get('profit_mechanism', 'غير محدد')}
الجمهور المستهدف: {analysis.get('', opportunity.get('target_audience', 'غير محدد'))}
استراتيجية التسعير: {plan.get('pricing_strategy', 'غير محدد')}
الزاوية المميزة: {analysis.get('unique_angle', 'غير محدد')}
توظيف الذكاء الاصطناعي: {analysis.get('ai_leverage', 'غير محدد')}

اكتب المحتوى بشكل كامل وجاهز للاستخدام الفوري.
استخدم اللغة العربية أو الإنجليزية حسب ما يناسب المنصة المستهدفة.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=EXECUTION_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    content = next(
        (b.text for b in response.content if b.type == "text"),
        "لم يتم إنشاء المحتوى",
    )

    return {
        **opportunity,
        "execution": {
            "type": output_type,
            "content": content,
        },
    }
