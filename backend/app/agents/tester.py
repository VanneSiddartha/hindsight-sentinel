from app.models.experience import WorkflowContext, AgentStep
from app.llm.gemini_client import analyze_workflow_agent


def run_tester_agent(context: WorkflowContext, force_failure: bool = False) -> AgentStep:
    """Evaluate known demo scenarios; otherwise report that repository tests are unavailable."""
    task = context.task_description
    recalled = context.recalled_experiences
    task_lower = task.lower()

    is_auth_scenario = "legacy auth" in task_lower or "auth middleware" in task_lower
    is_async_scenario = "async" in task_lower or "flaky" in task_lower
    is_config_scenario = "env" in task_lower or "misconfig" in task_lower
    is_demo_scenario = is_auth_scenario or is_async_scenario or is_config_scenario
    should_fail = force_failure or (is_demo_scenario and not recalled)
    observation = (
        f"Evaluating available workflow context for {context.workflow_type} of "
        f"'{context.service_name}' version '{context.version}' in '{context.environment}'."
    )

    if should_fail:
        if is_auth_scenario:
            test_output = (
                "SIMULATED FAILURE [Legacy auth compatibility scenario]\n"
                "Finding: The scenario omits the X-Legacy-Auth fallback required by the retained context.\n"
                "Result: Controlled demo scenario failed. No repository test suite was executed."
            )
            decision = "SIMULATION FAILED: Legacy-token compatibility scenario was not mitigated."
        elif is_async_scenario:
            test_output = (
                "SIMULATED FAILURE [Worker connection-pool scenario]\n"
                "Finding: The scenario has no connection-pool retry mitigation.\n"
                "Result: Controlled demo scenario failed. No repository load test was executed."
            )
            decision = "SIMULATION FAILED: Connection-pool scenario was not mitigated."
        elif is_config_scenario:
            test_output = (
                "SIMULATED FAILURE [Configuration scenario]\n"
                "Finding: Required environment configuration was not represented in the workflow context.\n"
                "Result: Controlled demo scenario failed. No repository test suite was executed."
            )
            decision = "SIMULATION FAILED: Configuration scenario requires environment validation."
        else:
            test_output = (
                "SIMULATED FAILURE [Replay control]\n"
                "The internal replay control requested a baseline failure.\n"
                "No repository test suite was executed."
            )
            decision = "SIMULATION FAILED: Internal closed-loop demo failure was requested."
        action_taken = "Recorded the simulated failure for experience extraction; no external test runner was invoked."
        status = "FAILED"
    elif is_demo_scenario:
        test_output = (
            "SIMULATED PASS [Known workflow scenario]\n"
            "A relevant Hindsight-informed mitigation is represented in the workflow plan.\n"
            "Result: Controlled demo scenario passed. No repository test suite was executed."
        )
        decision = f"SIMULATION PASSED: Relevant mitigation was represented ({len(recalled)} recalled experience(s))."
        action_taken = "Recorded the simulated scenario result for risk assessment."
        status = "SUCCESS"
    else:
        test_output = (
            "NOT RUN [Workflow analysis]\n"
            "No repository checkout or test runner is configured for this service.\n"
            "Actual test execution requires repository integration."
        )
        decision = "WARNING: This backend provides workflow analysis only and did not execute repository tests."
        action_taken = "Reported the validation limitation without claiming a test result."
        status = "WARNING"

    step = AgentStep(
        agent_name="tester",
        observation=observation,
        decision=decision,
        action_taken=action_taken,
        status=status,
        metadata={
            "test_output": test_output,
            "passed": status == "SUCCESS",
            "execution_mode": "simulated" if is_demo_scenario or force_failure else "analysis_only",
            "repository_tests_executed": False,
        },
    )
    analysis = analyze_workflow_agent(
        context,
        "tester",
        "Interpret only the supplied validation outcome and explain its limitations. Tests are simulated or not run; do not claim real tests ran or alter the deterministic status.",
        {
            "validation_status": status,
            "decision": decision,
            "validation_output": test_output,
            "repository_tests_executed": False,
        },
    )
    if analysis:
        context.gemini_reasoning.append(analysis)
        step.metadata["gemini_reasoning"] = analysis.model_dump()
    context.steps.append(step)
    return step
