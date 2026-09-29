from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline

def test_pipeline_execution():
    context = WorkflowContext(
        task_description="Deploy API v2 with legacy auth middleware",
        service_name="auth-service",
        environment="production"
    )
    
    result = execute_agent_pipeline(context)
    
    # Verify all 4 agents executed in order
    agent_names = [s.agent_name for s in result.steps]
    assert agent_names == ["planner", "coder", "tester", "security"]
    
    # Verify context status set
    assert result.status in ["PASSED", "FAILED", "BLOCKED_BY_RISK"]
    print("Pipeline Step 2 Test Passed! Steps logged:", agent_names)

if __name__ == "__main__":
    test_pipeline_execution()
