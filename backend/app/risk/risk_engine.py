from typing import Any, Dict, List, Optional, Tuple
from app.models.experience import WorkflowEvidence


def assess_workflow_risk(
    recalled_experiences: List[Dict[str, Any]],
    current_evidence: Optional[List[WorkflowEvidence]] = None,
) -> Tuple[str, List[WorkflowEvidence], str]:
    current_evidence = current_evidence or []
    historical_evidence: List[WorkflowEvidence] = []

    for experience in recalled_experiences:
        outcome = str(experience.get("outcome", "UNKNOWN")).upper()
        context = str(experience.get("context") or "Historical experience")
        lesson = experience.get("lesson")
        reason = (
            f"Historical outcome: {outcome}. "
            f"Lesson: {lesson}" if lesson else f"Historical outcome: {outcome}."
        )
        historical_evidence.append(WorkflowEvidence(
            source="historical",
            experience_id=experience.get("experience_id"),
            context=context,
            outcome=outcome,
            score=experience.get("score"),
            severity="high" if outcome == "FAILURE" else "caution",
            reason=reason,
            description=f"Related experience: {context}",
        ))

    serious_current_issue = any(item.severity == "high" for item in current_evidence)
    strong_failure_match = any(
        (item.outcome or "").upper() == "FAILURE"
        and item.score is not None
        and item.score >= 0.85
        for item in historical_evidence
    )

    if serious_current_issue:
        risk_level = "HIGH RISK"
        recommended_action = "Resolve the current validation failure before proceeding."
    elif strong_failure_match:
        risk_level = "HIGH RISK"
        matched = next(
            item for item in historical_evidence
            if (item.outcome or "").upper() == "FAILURE"
            and item.score is not None
            and item.score >= 0.85
        )
        recommended_action = (
            f"HIGH RISK DETECTED: a strong match to prior failure '{matched.experience_id}' was detected. "
            "Review the retained lesson and run targeted validation before proceeding."
        )
    elif historical_evidence or current_evidence:
        risk_level = "CAUTION"
        if historical_evidence:
            matched = historical_evidence[0]
            recommendation = matched.reason or "Review the relevant prior experience."
            recommended_action = (
                f"A related historical experience was found ({matched.experience_id}). "
                f"Review it and perform targeted validation. {recommendation}"
            )
        else:
            recommended_action = "Review the current workflow finding and perform targeted validation."
    else:
        risk_level = "NORMAL"
        recommended_action = "No known risk detected."

    return risk_level, historical_evidence, recommended_action


def evaluate_risk_rule(
    recalled_experiences: List[Dict[str, Any]],
    current_evidence: Optional[List[WorkflowEvidence]] = None,
) -> Tuple[str, List[Dict[str, Any]], str]:
    """Backward-compatible tuple interface for risk assessment consumers."""
    risk_level, historical, recommended_action = assess_workflow_risk(
        recalled_experiences,
        current_evidence,
    )
    evidence = [item.model_dump(exclude_none=True) for item in historical]
    evidence.extend(
        item.model_dump(exclude_none=True) for item in (current_evidence or [])
    )
    return risk_level, evidence, recommended_action
