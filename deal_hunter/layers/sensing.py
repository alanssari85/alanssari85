"""
Hunter Mode — Opportunity Discovery Layer

Scans for opportunities that can generate REAL money within 1–7 days.
Focus: Services · Arbitrage · B2B
Rejects: products, long dev cycles, >7 days to first payment
"""

from __future__ import annotations

import json
import anthropic


HUNTER_SYSTEM = """You are DealHunter AI operating in HUNTER MODE.

Your ONLY job: discover opportunities that produce REAL revenue within 1–7 days.

━━━ ACCEPT ━━━
• Services (freelance, consulting, done-for-you)
• Arbitrage (skill arbitrage, info arbitrage, buy-low-sell-high)
• B2B opportunities (businesses that need help RIGHT NOW)

━━━ REJECT — immediately discard if: ━━━
• Requires building a product or SaaS from scratch
• Time to first payment > 7 days
• Needs significant upfront capital
• Too saturated with zero differentiation angle
• Requires a team or complex infrastructure

Be SPECIFIC: exact service, exact customer, exact platform to find them.
Think like a salesperson, not an engineer.
"""


def run_sensing(
    client: anthropic.Anthropic,
    category: str,
) -> tuple[list[dict], list[dict]]:
    """
    Hunter Mode: scan a category for fast-money opportunities.

    Returns:
        (valid_opportunities, rejected_opportunities)
    """
    prompt = f"""
Hunt for profit opportunities in: **{category}**

For EACH opportunity you find, return a JSON object:
{{
  "name": "specific opportunity name",
  "source": "exact platform or channel",
  "description": "exactly what you do to make money — be specific",
  "target_audience": "specific customer type (industry, size, role)",
  "time_to_first_payment_days": <integer 1-7>,
  "why_now": "why this works in the current market",
  "rejected": false,
  "rejection_reason": null
}}

If an opportunity FAILS the criteria, still include it with:
  "rejected": true
  "rejection_reason": "exact reason"

Return a JSON array only. No explanations, no markdown.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=HUNTER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "[]"
    )

    start = text.find("[")
    end = text.rfind("]") + 1
    if start != -1 and end > start:
        try:
            all_opps = json.loads(text[start:end])
            valid = [o for o in all_opps if not o.get("rejected", False)]
            rejected = [o for o in all_opps if o.get("rejected", False)]
            for o in valid:
                o["category"] = category
            return valid, rejected
        except json.JSONDecodeError:
            pass

    return [], []
