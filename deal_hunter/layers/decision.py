"""
Layer 4 — Decision Engine
اختيار الفرص الأعلى درجة وتصفية الفرص غير المجدية.
"""

MIN_SCORE_THRESHOLD = 15.0
MAX_RISK_THRESHOLD = 8


def run_decision(opportunities: list[dict]) -> list[dict]:
    """
    Filter and rank opportunities by their final score.

    Rules:
    - Discard opportunities with final_score < MIN_SCORE_THRESHOLD
    - Discard opportunities with risk score > MAX_RISK_THRESHOLD
    - Sort by final_score descending
    - Return top candidates with decision metadata
    """
    decisions = []

    for opp in opportunities:
        scores = opp.get("scores", {})
        final_score = scores.get("final_score", 0)
        risk_score = scores.get("risk", {}).get("score", 10)

        if final_score < MIN_SCORE_THRESHOLD:
            decision = "مرفوض — درجة منخفضة"
            selected = False
        elif risk_score > MAX_RISK_THRESHOLD:
            decision = "مرفوض — مخاطرة عالية"
            selected = False
        else:
            verdict = scores.get("verdict", "متوسط")
            if final_score >= 22:
                decision = f"مختار — فرصة ممتازة ({verdict})"
                selected = True
            elif final_score >= 17:
                decision = f"مختار — فرصة جيدة ({verdict})"
                selected = True
            else:
                decision = f"مشروط — يحتاج مراجعة ({verdict})"
                selected = True

        decisions.append({
            **opp,
            "decision": decision,
            "selected": selected,
        })

    # Sort by final_score descending
    decisions.sort(
        key=lambda x: x.get("scores", {}).get("final_score", 0),
        reverse=True,
    )

    return decisions
