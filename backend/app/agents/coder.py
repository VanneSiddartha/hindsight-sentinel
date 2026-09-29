from app.models.experience import WorkflowContext, AgentStep
from app.llm.gemini_client import analyze_workflow_agent

def run_coder_agent(context: WorkflowContext) -> AgentStep:
    """
    Coder Agent: Translates the Planner roadmap into specific code modifications & diffs.
    Incorporate Hindsight memory lessons directly into code patch generation.
    """
    task = context.task_description
    recalled = context.recalled_experiences
    planner_step = next((s for s in context.steps if s.agent_name == "planner"), None)
    
    observation = (
        f"Processing the simulated workflow-analysis plan for {context.workflow_type} "
        f"of {context.service_name} {context.version} in {context.environment}."
    )
    if recalled:
        observation += f" Active Hindsight Memory Lesson: '{recalled[0].get('lesson')}'"
    
    # Generate diff based on task and memory status
    if "legacy auth" in task.lower() or "auth middleware" in task.lower():
        if recalled:
            code_diff = (
                "--- api/v2/auth.py\n"
                "+++ api/v2/auth.py\n"
                "@@ -14,3 +14,6 @@\n"
                " def verify_v2_token(req, fallback_to_legacy=True):\n"
                "+    # Hindsight Precedent [" + recalled[0].get('experience_id', 'exp-01') + "]: Preserving legacy fallback\n"
                "+    if not req.headers.get('Authorization') and fallback_to_legacy:\n"
                "+        return legacy_auth_provider.validate(req.headers.get('X-Legacy-Auth'))\n"
            )
            decision = f"Memory-Informed Patch: Added X-Legacy-Auth fallback in api/v2/auth.py as instructed by Hindsight [{recalled[0].get('experience_id')}]."
            action_taken = "Simulated a backward-compatible auth patch with legacy header fallback."
        else:
            code_diff = (
                "--- api/v2/auth.py\n"
                "+++ api/v2/auth.py\n"
                "@@ -14,3 +14,4 @@\n"
                "- def verify_v2_token(req, fallback_to_legacy=True):\n"
                "+ def verify_v2_token(req):\n"
                "+     # Stripped legacy auth headers per unmitigated baseline plan\n"
            )
            decision = "Baseline Patch: Stripped legacy authorization headers from api/v2/auth.py."
            action_taken = "Simulated an unmitigated patch omitting legacy auth headers."
    elif "async" in task.lower() or "flaky" in task.lower():
        if recalled:
            code_diff = (
                "--- worker/pool.py\n"
                "+++ worker/pool.py\n"
                "@@ -8,2 +8,4 @@\n"
                "+ # Hindsight Precedent: 300ms exponential retry policy\n"
                "+ connection_pool.set_retry_policy(max_retries=3, backoff_ms=300)\n"
            )
            decision = "Memory-Informed Patch: Added 300ms exponential retry policy to connection pool."
            action_taken = "Simulated a connection pool retry handler."
        else:
            code_diff = (
                "--- worker/pool.py\n"
                "+++ worker/pool.py\n"
                "@@ -8,2 +8,3 @@\n"
                "+ # Worker listener without retry handler\n"
            )
            decision = "Baseline Patch: Applied worker patch without retry handler."
            action_taken = "Simulated an unmitigated worker patch."
    else:
        code_diff = (
            f"--- src/services/{context.service_name}.py\n"
            f"+++ src/services/{context.service_name}.py\n"
            "@@ -1,3 +1,5 @@\n"
            f"+ # Workflow analysis only; no repository code was modified.\n"
        )
        decision = f"Prepared a controlled workflow-analysis simulation for {context.service_name}; no repository contents were accessed."
        action_taken = "Simulated the planned change; no files or services were modified."

    step = AgentStep(
        agent_name="coder",
        observation=observation,
        decision=decision,
        action_taken=action_taken,
        status="SUCCESS",
        metadata={
            "diff": code_diff,
            "memory_influenced": bool(recalled),
            "execution_mode": "simulated",
            "repository_accessed": False,
        }
    )
    analysis = analyze_workflow_agent(
        context,
        "coder",
        "Review the simulated change/action for consistency with the planner and relevant Hindsight lessons. This system does not access or modify repository files; do not write code.",
        {
            "planner_decision": planner_step.decision if planner_step else None,
            "simulated_decision": decision,
            "simulated_action": action_taken,
        },
    )
    if analysis:
        context.gemini_reasoning.append(analysis)
        step.metadata["gemini_reasoning"] = analysis.model_dump()
    context.steps.append(step)
    return step
