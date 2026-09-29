from app.experience.seed import seed_hindsight_experiences
from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline

def test_replay_before_after():
    # Seed memories
    seed_hindsight_experiences()
    
    # Phase 1: Baseline run with recall OFF
    ctx1 = WorkflowContext(
        task_description="Deploy API v2 endpoint with legacy auth middleware",
        service_name="payment-auth"
    )
    result1 = execute_agent_pipeline(ctx1, force_failure=True, enable_recall=False)
    assert result1.risk_level == "HIGH RISK"
    assert len(result1.risk_evidence) == 0
    assert result1.current_evidence[0].source == "current"
    assert result1.status == "FAILED"
    
    # Phase 2: Interception run with recall ON
    ctx2 = WorkflowContext(
        task_description="Deploy API v2 endpoint with legacy auth middleware",
        service_name="payment-auth"
    )
    result2 = execute_agent_pipeline(ctx2, enable_recall=True)
    assert result2.risk_level == "HIGH RISK"
    assert len(result2.risk_evidence) > 0
    assert result2.status == "BLOCKED_BY_RISK"
    
    print("Step 6 Replay Test Passed! Baseline validation fails; Hindsight-influenced replay is risk-gated.")

if __name__ == "__main__":
    test_replay_before_after()
