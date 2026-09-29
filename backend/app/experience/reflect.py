import os
import logging
from typing import List, Dict, Any, Tuple
from app.experience.retain import get_hindsight_client
from app.models.experience import WorkflowEvidence
from app.risk.risk_engine import assess_workflow_risk

logger = logging.getLogger(__name__)

def reflect_on_experience(
    current_context: str,
    recalled: List[Dict[str, Any]],
    current_evidence: List[WorkflowEvidence] | None = None,
) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    Reflect Step: Uses official Hindsight SDK reflect() method or structured risk reasoning
    over recalled memories and task context.
    Returns: (risk_level, supporting_evidence, recommended_action)
    """
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    client = get_hindsight_client()
    
    # Try official Hindsight reflect SDK call first
    if client and recalled:
        try:
            hindsight_reflect = client.reflect(bank_id=bank_id, query=current_context)
            if hindsight_reflect and hasattr(hindsight_reflect, "answer"):
                logger.info("Hindsight reflection completed.")
        except Exception as e:
            logger.warning("Hindsight reflection failed; using a factual local reflection: %s", e)

    risk_level, historical_evidence, recommendation = assess_workflow_risk(recalled, current_evidence)
    evidence = [item.model_dump(exclude_none=True) for item in historical_evidence]
    evidence.extend(
        item.model_dump(exclude_none=True) for item in (current_evidence or [])
    )
    return risk_level, evidence, recommendation

def explain_experience_relevance(
    current_context: str,
    recalled: List[Dict[str, Any]],
) -> str | None:
    if not recalled:
        return None

    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    client = get_hindsight_client()
    if client:
        try:
            result = client.reflect(bank_id=bank_id, query=current_context)
            answer = getattr(result, "answer", None)
            if isinstance(answer, str) and answer.strip():
                return answer.strip()
        except Exception as error:
            logger.warning("Hindsight reflection unavailable; explaining retrieved memory directly: %s", error)

    memory = recalled[0]
    parts = [
        f"Hindsight retrieved experience {memory.get('experience_id', 'without an ID')} as related context.",
        f"Prior context: {memory.get('context', 'not provided')}.",
        f"Prior outcome: {memory.get('outcome', 'not provided')}.",
    ]
    if memory.get("lesson"):
        parts.append(f"Retained lesson: {memory['lesson']}.")
    parts.append(
        "This is historical context for review and does not establish that the current workflow will fail."
    )
    return " ".join(parts)
