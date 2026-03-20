"""
Evaluator Mode — Opportunity Scoring Engine

Scores each opportunity on 5 criteria (0–10 each):
  1. profit_potential      — how much money can this make?
  2. ease_of_execution     — how easy is it to start and deliver?
  3. speed_to_first_payment — how fast can you get paid? (10 = same day)
  4. competition_level     — how crowded is this? (10 = no competition)
  5. risk_level            — how safe is it? (10 = nearly zero risk)

final_score = sum of all 5 (max = 50)
"""

from __future__ import annotations

import json
import anthropic


EVALUATOR_SYSTEM = """You are DealHunter AI operating in EVALUATOR MODE.

Your job: score opportunities with ruthless objectivity.

Scoring rules:
- profit_potential      (0-10): 10 = $500+/week easily, 0 = barely pays
- ease_of_execution     (0-10): 10 = anyone can do it today, 0 = requires rare skills
- speed_to_first_payment(0-10): 10 = paid within 24 hours, 0 = 30+ days
- competition_level     (0-10): 10 = blue ocean, 0 = brutal red ocean
- risk_level            (0-10): 10 = zero risk, 0 = could lose money

Be HONEST. Overestimating scores wastes execution time on bad opportunities.
Think like an investor evaluating a deal, not a cheerleader.
"""


def run_scoring(client: anthropic.Anthropic, opportunity: dict) -> dict:
    """
    Evaluator Mode: score a single opportunity on 5 criteria.
    Returns opportunity dict enriched with 'scores' and 'final_score'.
    """
    prompt = f"""
Evaluate this opportunity:

Name: {opportunity.get('name', 'N/A')}
Source: {opportunity.get('source', 'N/A')}
Description: {opportunity.get('description', 'N/A')}
Target audience: {opportunity.get('target_audience', 'N/A')}
Time to first payment: {opportunity.get('time_to_first_payment_days', '?')} days
Why now: {opportunity.get('why_now', 'N/A')}

Return ONLY this JSON (no markdown, no extra text):
{{
  "profit_potential": {{
    "score": <0-10>,
    "reason": "<one sentence>"
  }},
  "ease_of_execution": {{
    "score": <0-10>,
    "reason": "<one sentence>"
  }},
  "speed_to_first_payment": {{
    "score": <0-10>,
    "reason": "<one sentence>"
  }},
  "competition_level": {{
    "score": <0-10>,
    "reason": "<one sentence>"
  }},
  "risk_level": {{
    "score": <0-10>,
    "reason": "<one sentence>"
  }}
}}
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=EVALUATOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    scores: dict = {}
    if start != -1 and end > start:
        try:
            scores = json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # Calculate final score (max = 50)
    total = sum(
        scores.get(k, {}).get("score", 0)
        for k in (
            "profit_potential",
            "ease_of_execution",
            "speed_to_first_payment",
            "competition_level",
            "risk_level",
        )
    )
    scores["final_score"] = round(total, 1)

    return {**opportunity, "scores": scores}
