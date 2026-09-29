from app.models.experience import WorkflowContext, WorkflowEvidence
from app.experience.recall import build_workflow_recall_query, recall_experiences_with_status
from app.experience.reflect import explain_experience_relevance
from app.risk.risk_engine import assess_workflow_risk
from app.agents.planner import run_planner_agent
from app.agents.coder import run_coder_agent
from app.agents.tester import run_tester_agent
from app.agents.security import run_security_agent
from app.experience.extract import extract_experience_from_workflow
from app.llm.gemini_client import configured_model, is_configured


def execute_agent_pipeline(
    context: WorkflowContext,
    force_failure: bool = False,
    enable_recall: bool = True,
) -> WorkflowContext:
    """Run Hindsight recall, four agent analyses, risk assessment, and retention."""
    context.status = "IN_PROGRESS"
    context.llm.model = configured_model()
    context.llm.status = "ready" if is_configured() else "not_configured"
    recall_query = build_workflow_recall_query(context)

    if enable_recall:
        recalled, hindsight_available, hindsight_message = recall_experiences_with_status(
            recall_query,
            service_name=context.service_name,
        )
        context.recalled_experiences = recalled
        context.hindsight_available = hindsight_available
        context.hindsight_message = hindsight_message
        context.hindsight_reflection = explain_experience_relevance(recall_query, recalled)
    else:
        context.recalled_experiences = []
        context.hindsight_available = False
        context.hindsight_message = "Hindsight recall was disabled for this internal replay run."
        context.hindsight_reflection = None

    # This preliminary assessment lets the Planner and Security agent reason over
    # historical context. It is recalculated after the Tester reports current evidence.
    risk_level, _, recommendation = assess_workflow_risk(context.recalled_experiences)
    context.risk_level = risk_level
    context.recommended_action = recommendation

    run_planner_agent(context)
    run_coder_agent(context)
    tester_step = run_tester_agent(context, force_failure=force_failure)

    context.current_evidence = []
    if tester_step.status == "FAILED":
        context.current_evidence.append(WorkflowEvidence(
            source="current",
            severity="high",
            description="The controlled workflow validation scenario reported a failure.",
            reason=tester_step.decision,
        ))
    elif tester_step.status == "WARNING":
        context.current_evidence.append(WorkflowEvidence(
            source="current",
            severity="caution",
            description="Repository validation could not be performed.",
            reason=tester_step.decision,
        ))

    risk_level, historical_evidence, recommendation = assess_workflow_risk(
        context.recalled_experiences,
        context.current_evidence,
    )
    context.risk_level = risk_level
    context.risk_evidence = historical_evidence
    context.recommended_action = recommendation

    security_step = run_security_agent(context)

    if tester_step.status == "FAILED":
        context.status = "FAILED"
        context.outcome = "FAILURE"
    elif context.risk_level == "HIGH RISK":
        context.status = "BLOCKED_BY_RISK"
        context.outcome = "BLOCKED"
    elif tester_step.status == "WARNING" or security_step.status == "WARNING":
        context.status = "COMPLETED_WITH_WARNING"
        context.outcome = "ANALYZED"
    else:
        context.status = "PASSED"
        context.outcome = "SUCCESS"

    extracted = extract_experience_from_workflow(context)
    if extracted is not None and context.retention_status == "local_only":
        context.hindsight_message = (
            "Remote Hindsight is unavailable; the new experience was retained in the local vault only."
        )
    return context
