from app.models.experience import WorkflowContext, AgentStep
from app.llm.gemini_client import analyze_workflow_agent

def run_security_agent(context: WorkflowContext) -> AgentStep:
    """
    Security Agent: Conducts security policy audit, static security scan (SAST),
    and risk policy compliance checks before deployment clearance.
    """
    tester_step = next((s for s in context.steps if s.agent_name == "tester"), None)
    
    observation = (
        f"Reviewing security-relevant workflow context for {context.workflow_type} of "
        f"'{context.service_name}' version '{context.version}' in '{context.environment}'."
    )
    
    if tester_step and tester_step.status == "FAILED":
        decision = "SECURITY REJECTED: Upstream test failure detected. Security scan aborted."
        action_taken = "Blocked pipeline deployment until test regressions are resolved."
        status = "SKIPPED"
    elif context.risk_level == "HIGH RISK":
        decision = (
            "SECURITY WARNING / CONDITIONAL BLOCK:\n"
            "The risk engine identified elevated risk from current validation or relevant historical evidence. "
            "This simulation cannot perform a repository security scan or deployment."
        )
        action_taken = "Recommended review of evidence before any real deployment."
        status = "WARNING"
    else:
        decision = (
            "SECURITY REVIEW LIMITED: No repository contents or infrastructure were inspected, "
            "so vulnerability status cannot be determined."
        )
        action_taken = "Run repository and infrastructure security scanners before a real deployment."
        status = "WARNING"

    step = AgentStep(
        agent_name="security",
        observation=observation,
        decision=decision,
        action_taken=action_taken,
        status=status,
        metadata={
            "risk_level": context.risk_level,
            "repository_scanned": False,
            "execution_mode": "analysis_only",
        }
    )
    analysis = analyze_workflow_agent(
        context,
        "security",
        "Review only the supplied workflow/test/risk evidence for security-relevant considerations. Do not invent vulnerabilities or claim repository/security scans ran. Gemini must not assign or change risk level.",
        {
            "risk_level_from_risk_engine": context.risk_level,
            "risk_evidence": [
                item.model_dump(exclude_none=True) for item in context.risk_evidence
            ],
            "current_evidence": [
                item.model_dump(exclude_none=True) for item in context.current_evidence
            ],
            "security_review": decision,
            "repository_scanned": False,
        },
    )
    if analysis:
        context.gemini_reasoning.append(analysis)
        step.metadata["gemini_reasoning"] = analysis.model_dump()
    context.steps.append(step)
    return step
