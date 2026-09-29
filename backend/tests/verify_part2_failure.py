import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline

def run_controlled_failure_test():
    print("=== PART 2: CONTROLLED FAILURE TEST ===")
    task = "Deploy database migration with invalid connection string parameters"
    ctx = WorkflowContext(task_description=task, service_name="db-service")
    
    # Execute workflow with force_failure=True to guarantee TESTER -> FAILED
    result = execute_agent_pipeline(ctx, force_failure=True, enable_recall=False)
    
    tester_step = next(s for s in result.steps if s.agent_name == "tester")
    print(f"Workflow ID: {result.workflow_id}")
    print(f"Workflow Final Status: {result.status}")
    print(f"Tester Agent Status: {tester_step.status}")
    print(f"Tester Output:\n{tester_step.metadata.get('test_output')}")
    
    assert tester_step.status == "FAILED"
    assert result.status == "FAILED"
    print("PART 2 VERIFICATION SUCCESSFUL: Controlled failure produced TESTER -> FAILED!")
    return result

if __name__ == "__main__":
    run_controlled_failure_test()
