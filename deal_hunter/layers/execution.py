"""
Closer Mode — Convert the Winner Into a READY-TO-SELL Offer

Mandatory output (as requested):
  opportunity, target_customer, pain_point, solution,
  value_proposition, how_it_makes_money, pricing_model,
  expected_earnings_7_days, execution_plan, sales_message, confidence

My additions (make it truly sales-ready):
  top_objections         — the 3 objections buyers will raise
  objection_responses    — how to crush each objection
  outreach_channels      — exactly where to find the target customer
  follow_up_sequence     — 3-step follow-up if no reply
"""

from __future__ import annotations

import json
import anthropic


CLOSER_SYSTEM = """You are DealHunter AI operating in CLOSER MODE.

Your job: transform a raw opportunity into a READY-TO-SELL offer.

Rules:
- Think like a TOP salesperson, not an engineer
- Every word must serve the sale
- Be specific: no vague platitudes, no generic statements
- The sales_message must be copy-paste ready (< 150 words)
- execution_plan must have exactly 5 steps, each completable within 24 hours
- expected_earnings_7_days must be a realistic dollar range, not a dream
- confidence must reflect reality (70–90% is honest, 99% is a lie)
"""


def run_execution(client: anthropic.Anthropic, winner: dict) -> dict:
    """
    Closer Mode: generate a complete sellable offer for the winning opportunity.
    Returns a dict with 'offer' key containing the full JSON offer.
    """
    scores = winner.get("scores", {})

    prompt = f"""
Convert this winning opportunity into a ready-to-sell offer:

Opportunity: {winner.get('name', 'N/A')}
Description: {winner.get('description', 'N/A')}
Target audience: {winner.get('target_audience', 'N/A')}
Source / platform: {winner.get('source', 'N/A')}
Why now: {winner.get('why_now', 'N/A')}
Time to first payment: {winner.get('time_to_first_payment_days', '?')} days
Profit potential score: {scores.get('profit_potential', {}).get('score', 'N/A')}/10
Ease score: {scores.get('ease_of_execution', {}).get('score', 'N/A')}/10

Return ONLY this JSON (no markdown, no extra text):
{{
  "opportunity": "<name of the opportunity>",
  "target_customer": "<specific customer profile: industry, company size, role, pain trigger>",
  "pain_point": "<the exact problem they are losing money or time over>",
  "solution": "<exactly what you deliver and how — one clear sentence>",
  "value_proposition": "<result + timeframe + differentiator, e.g. 'We double your lead volume in 30 days using AI, with zero extra headcount'>",
  "how_it_makes_money": "<step-by-step: find client → deliver → collect payment>",
  "pricing_model": "<exact pricing: e.g. '$500 flat fee', '$1,500/month retainer', '20% of revenue generated'>",
  "expected_earnings_7_days": "<realistic range, e.g. '$500–$2,000 from 1–2 clients'>",
  "execution_plan": [
    "Step 1 (Day 1): <specific action>",
    "Step 2 (Day 1–2): <specific action>",
    "Step 3 (Day 2–3): <specific action>",
    "Step 4 (Day 3–5): <specific action>",
    "Step 5 (Day 5–7): <specific action>"
  ],
  "sales_message": "<copy-paste ready cold outreach message, max 150 words, conversational tone, ends with one clear call to action>",
  "confidence": "<percentage, e.g. '82%'>",
  "top_objections": [
    "<objection 1>",
    "<objection 2>",
    "<objection 3>"
  ],
  "objection_responses": [
    "<response to objection 1>",
    "<response to objection 2>",
    "<response to objection 3>"
  ],
  "outreach_channels": [
    "<channel 1: e.g. LinkedIn Sales Navigator — search by job title + industry>",
    "<channel 2>",
    "<channel 3>"
  ],
  "follow_up_sequence": [
    "Day 2: <follow-up message if no reply>",
    "Day 5: <second follow-up — add new value>",
    "Day 10: <final break-up message that often triggers replies>"
  ]
}}
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        system=CLOSER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    offer: dict = {}
    if start != -1 and end > start:
        try:
            offer = json.loads(text[start:end])
        except json.JSONDecodeError:
            # If JSON parsing fails, store raw text for debugging
            offer = {"raw": text, "parse_error": True}

    return {**winner, "offer": offer}
