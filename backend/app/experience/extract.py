from typing import Optional

from app.experience.retain import retain_experience
from app.models.experience import ExperienceAgentActivity, ExperienceModel, WorkflowContext


def extract_experience_from_workflow(context: WorkflowContext) -> Optional[ExperienceModel]:
    """Create an experience from observed workflow steps and their reported outcome."""
    if not context.steps or context.outcome not in {"SUCCESS", "FAILURE", "BLOCKED", "ANALYZED"}:
        return None

    tester_step = next((step for step in context.steps if step.agent_name == "tester"), None)
    if tester_step is None:
        return None

    planner_step = next((step for step in context.steps if step.agent_name == "planner"), None)
    coder_step = next((step for step in context.steps if step.agent_name == "coder"), None)
    validation = tester_step.metadata.get("test_output") or tester_step.decision

    if context.outcome == "FAILURE":
        lesson = f"Validation reported a failure: {tester_step.decision}"
    elif context.outcome == "SUCCESS":
        lesson = f"Validation reported success: {tester_step.decision}"
    elif context.outcome == "BLOCKED":
        lesson = f"The workflow was blocked by risk assessment: {context.recommended_action or context.status}."
    else:
        lesson = f"Repository validation was not run: {tester_step.decision}"

    experience = ExperienceModel(
        experience_id=f"exp-{context.workflow_id}",
        context=(
            f"{context.workflow_type.replace('_', ' ').title()} of {context.service_name} "
            f"{context.version} in {context.environment}. Task: {context.task_description}"
        ),
        service_name=context.service_name,
        agents_involved=list(dict.fromkeys(step.agent_name for step in context.steps)),
        decision=planner_step.decision if planner_step else "No planner decision was recorded.",
        action=coder_step.action_taken if coder_step else "No coder action was recorded.",
        validation=validation,
        outcome=context.outcome,
        root_cause=None,
        lesson=lesson,
        future_applicability=f"{context.workflow_type.replace('_', ' ')} workflows for {context.service_name}",
        workflow_id=context.workflow_id,
        workflow_type=context.workflow_type,
        task_description=context.task_description,
        version=context.version,
        environment=context.environment,
        agent_activities=[
            ExperienceAgentActivity(
                agent_name=step.agent_name,
                decision=step.decision,
                action=step.action_taken,
                status=step.status,
            )
            for step in context.steps
        ],
        tags=[context.service_name, context.workflow_type, context.outcome.lower()],
        source="workflow",
    )

    retention = retain_experience(experience)
    context.extracted_experience = experience
    context.metadata_status = retention["metadata_status"]
    context.hindsight_retention_status = retention["hindsight_status"]
    context.retention_status = (
        "remote"
        if retention["remote_synced"]
        else "local_only"
        if retention["metadata_saved"]
        else "temporary"
    )
    context.hindsight_available = bool(retention["remote_synced"])
    if retention["message"]:
        context.hindsight_message = retention["message"]
    return experience
