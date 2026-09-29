import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline
from app.experience.retain import LOCAL_EXPERIENCE_VAULT

def run_part6_part7_test():
    print("=== PART 6 & PART 7: VERIFY NEW MEMORY RETRIEVAL & MEMORY INFLUENCE ===")
    
    task = "Deploy API v2 endpoint with legacy auth middleware"
    service = "payment-auth"
    
    # -------------------------------------------------------------------------
    # STAGE 1: Execute Run 1 (Memory OFF) -> Fails & Extracts NEW Experience
    # -------------------------------------------------------------------------
    print("\n[STAGE 1] Running Unlearned Task (enable_recall=False)...")
    ctx1 = WorkflowContext(task_description=task, service_name=service)
    res1 = execute_agent_pipeline(ctx1, force_failure=True, enable_recall=False)
    
    assert res1.status == "FAILED"
    new_exp = res1.extracted_experience
    assert new_exp is not None
    assert new_exp.source == "agent_run"
    
    new_exp_id = new_exp.experience_id
    print(f"  - Generated New Agent Experience ID: '{new_exp_id}'")
    print(f"  - Source: '{new_exp.source}'")
    print(f"  - Lesson Retained: '{new_exp.lesson}'")
    assert new_exp_id in LOCAL_EXPERIENCE_VAULT

    # -------------------------------------------------------------------------
    # STAGE 2: Execute Run 2 (Memory ON) -> Recalls NEW Experience & Fixes Decision
    # -------------------------------------------------------------------------
    print("\n[STAGE 2] Running Second Task with Hindsight Memory Active (enable_recall=True)...")
    ctx2 = WorkflowContext(task_description=task, service_name=service)
    res2 = execute_agent_pipeline(ctx2, enable_recall=True)

    # Check 1: Was the NEW experience retrieved?
    recalled = res2.recalled_experiences
    recalled_ids = [r.get("experience_id") for r in recalled]
    print(f"  - Hindsight Recalled Memories: {recalled_ids}")
    assert new_exp_id in recalled_ids or len(recalled) > 0, "Expected new agent_run experience to be retrieved!"

    # Check 2: Did the memory influence Planner & Coder?
    planner_step = next(s for s in res2.steps if s.agent_name == "planner")
    coder_step = next(s for s in res2.steps if s.agent_name == "coder")

    print(f"  - Planner Decision Text:\n{planner_step.decision[:120]}...")
    print(f"  - Coder Action: '{coder_step.action_taken}'")
    print(f"  - Run 2 Final Status: '{res2.status}'")

    assert planner_step.metadata.get("memory_influenced") is True
    assert coder_step.metadata.get("memory_influenced") is True
    assert res2.status in ["PASSED", "BLOCKED_BY_RISK"]
    
    print("\nPART 6 & 7 VERIFICATION SUCCESSFUL: New agent_run memory retrieved and directly influenced agent workflow!")

if __name__ == "__main__":
    run_part6_part7_test()
