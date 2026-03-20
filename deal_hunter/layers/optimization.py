"""
Optimization Layer — Learn and Improve for Next Session

Analyzes all evaluated opportunities (not just the winner) to extract
patterns and recommendations for the next hunting cycle.
"""

from __future__ import annotations

import json
import anthropic


OPTIMIZATION_SYSTEM = """You are DealHunter AI in OPTIMIZATION MODE.

Analyze this session's results and extract actionable lessons.
Be brutally honest about what patterns emerged.
Output only what will make the NEXT session more profitable.
"""


def run_optimization(
    client: anthropic.Anthropic,
    all_scored: list[dict],
    winner: dict,
    rejected_log: list[dict],
) -> dict:
    """
    Analyze session results and produce next-cycle recommendations.
    """
    summary = []
    for opp in all_scored:
        scores = opp.get("scores", {})
        summary.append({
            "name": opp.get("name", "N/A"),
            "category": opp.get("category", "N/A"),
            "final_score": scores.get("final_score", 0),
            "profit_potential": scores.get("profit_potential", {}).get("score", 0),
            "ease": scores.get("ease_of_execution", {}).get("score", 0),
            "speed": scores.get("speed_to_first_payment", {}).get("score", 0),
            "competition": scores.get("competition_level", {}).get("score", 0),
            "risk": scores.get("risk_level", {}).get("score", 0),
        })

    prompt = f"""
Session summary:
- Total opportunities evaluated: {len(all_scored)}
- Opportunities rejected by Hunter (before scoring): {len(rejected_log)}
- Winner: {winner.get('name', 'N/A')} (score: {winner.get('scores', {}).get('final_score', 0)}/50)

Scored opportunities:
{json.dumps(summary, ensure_ascii=False, indent=2)}

Return ONLY this JSON:
{{
  "winning_pattern": "<what made the winner better than the rest — one insight>",
  "worst_categories": ["<category that consistently scored low>"],
  "best_categories": ["<category that consistently scored high>"],
  "common_rejection_reason": "<most frequent reason opportunities were rejected>",
  "next_session_focus": [
    "<specific action 1 to find better opportunities next time>",
    "<specific action 2>",
    "<specific action 3>"
  ],
  "categories_to_add": ["<new category to explore next session>"],
  "categories_to_drop": ["<category that wasted time this session>"],
  "estimated_improvement_next_session": "<e.g. 'expect 20% higher winner score by focusing on X'>"
}}
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=OPTIMIZATION_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )

    start = text.find("{")
    end = text.rfind("}") + 1
    report: dict = {}
    if start != -1 and end > start:
        try:
            report = json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return report
