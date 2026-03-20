"""
Decision Engine — Pick ONE Winner

Rules:
- Must have final_score >= 30 (out of 50) to qualify
- Must have risk_level score >= 5 (not too risky)
- Pick the single highest-scoring opportunity
- If nothing qualifies, lower threshold to >= 25 and retry
- If still nothing, return the best available with a warning
"""

from __future__ import annotations

MIN_SCORE = 30.0
MIN_SCORE_FALLBACK = 25.0
MIN_RISK_SCORE = 5


def run_decision(opportunities: list[dict]) -> dict:
    """
    Pick exactly ONE winning opportunity from the scored list.

    Returns a dict with:
      - 'winner': the selected opportunity dict
      - 'runner_ups': the rest, sorted by score
      - 'selection_note': explanation of the decision
    """
    if not opportunities:
        return {"winner": None, "runner_ups": [], "selection_note": "No opportunities to evaluate."}

    # Sort by final_score descending
    ranked = sorted(
        opportunities,
        key=lambda x: x.get("scores", {}).get("final_score", 0),
        reverse=True,
    )

    def qualifies(opp: dict, threshold: float) -> bool:
        scores = opp.get("scores", {})
        final = scores.get("final_score", 0)
        risk = scores.get("risk_level", {}).get("score", 0)
        return final >= threshold and risk >= MIN_RISK_SCORE

    # Try strict threshold first
    qualified = [o for o in ranked if qualifies(o, MIN_SCORE)]
    note = f"Selected from {len(qualified)} qualifying opportunities (score ≥ {MIN_SCORE}/50)."

    if not qualified:
        # Fallback threshold
        qualified = [o for o in ranked if qualifies(o, MIN_SCORE_FALLBACK)]
        note = (
            f"No opportunity met the strict threshold ({MIN_SCORE}/50). "
            f"Selected best available (score ≥ {MIN_SCORE_FALLBACK}/50)."
        )

    if not qualified:
        # Last resort: just pick the highest scorer with a warning
        qualified = [ranked[0]]
        note = (
            "WARNING: No opportunity met minimum quality thresholds. "
            "Selecting highest scorer. Review results carefully before executing."
        )

    winner = qualified[0]
    runner_ups = [o for o in ranked if o is not winner]

    return {
        "winner": winner,
        "runner_ups": runner_ups,
        "selection_note": note,
    }
