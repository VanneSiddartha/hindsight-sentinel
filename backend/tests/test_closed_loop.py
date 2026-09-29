import sys
import os

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline
from app.experience.retain import LOCAL_EXPERIENCE_VAULT

def test_complete_closed_loop_memory_cycle():
    print("\n=================================================================")
    print(" AgentVault Closed-Loop Memory Test (Run 1 -> Run 2)             ")
    print("=================================================================")

    task_description = "Upgrade auth middleware for API v2 migration"
    service_name = "payment-auth"

    # -------------------------------------------------------------------------
    # RUN 1: Unlearned Attempt (Memory OFF)
    # -------------------------------------------------------------------------
    print("\n[RUN 1] Executing Unlearned Task (enable_recall=False)...")
    ctx_run1 = WorkflowContext(
        task_description=task_description,
        service_name=service_name
    )
    result_run1 = execute_agent_pipeline(ctx_run1, force_failure=True, enable_recall=False)

    # Acceptance Criteria Check 1: Run 1 Fails and Extracts Experience
    assert result_run1.status == "FAILED", f"Expected Run 1 status FAILED, got {result_run1.status}"
    assert result_run1.extracted_experience is not None, "Expected extracted_experience to be created post-run"
    
    extracted_exp = result_run1.extracted_experience
    assert extracted_exp.source == "workflow", f"Expected source 'workflow', got {extracted_exp.source}"
    assert extracted_exp.workflow_id == result_run1.workflow_id
    assert extracted_exp.outcome == "FAILURE", f"Expected outcome 'FAILURE', got {extracted_exp.outcome}"
    assert "legacy auth" in extracted_exp.lesson.lower() or "legacy" in extracted_exp.lesson.lower(), "Expected lesson to mention legacy auth"
    
    # Check experience retained in vault / Hindsight
    assert extracted_exp.experience_id in LOCAL_EXPERIENCE_VAULT
    print("  [OK] Run 1 Failed as expected.")
    print(f"  [OK] Extracted new Experience (ID: '{extracted_exp.experience_id}', Source: '{extracted_exp.source}').")
    print(f"  [OK] Retained Lesson in Hindsight: '{extracted_exp.lesson}'")

    # -------------------------------------------------------------------------
    # RUN 2: Memory-Informed Attempt (Memory ON)
    # -------------------------------------------------------------------------
    print("\n[RUN 2] Executing Same Task with Hindsight Memory Active (enable_recall=True)...")
    ctx_run2 = WorkflowContext(
        task_description=task_description,
        service_name=service_name
    )
    result_run2 = execute_agent_pipeline(ctx_run2, enable_recall=True)

    # Acceptance Criteria Check 2: Memory Recalled & Injected
    assert len(result_run2.recalled_experiences) > 0, "Expected Hindsight to recall past experiences"
    recalled_ids = [e["experience_id"] for e in result_run2.recalled_experiences]
    print(f"  [OK] Hindsight Recalled Memories: {recalled_ids}")

    # Acceptance Criteria Check 3: Planner & Coder Influenced by Memory
    planner_step = next(s for s in result_run2.steps if s.agent_name == "planner")
    coder_step = next(s for s in result_run2.steps if s.agent_name == "coder")

    assert planner_step.metadata.get("memory_influenced") is True, "Expected Planner step to be memory influenced"
    assert "MEMORY INFLUENCE" in planner_step.decision or "Hindsight" in planner_step.decision, "Expected Planner decision text to reference memory influence"
    assert "fallback" in planner_step.decision.lower() or "legacy" in planner_step.decision.lower(), "Expected Planner decision to preserve fallback"

    assert coder_step.metadata.get("memory_influenced") is True, "Expected Coder step to be memory influenced"
    assert "fallback" in coder_step.action_taken.lower() or "legacy" in coder_step.action_taken.lower(), "Expected Coder patch to preserve legacy fallback"

    # Acceptance Criteria Check 4: Test Passed!
    assert result_run2.status in ["PASSED", "BLOCKED_BY_RISK"], f"Expected Run 2 status PASSED or BLOCKED_BY_RISK, got {result_run2.status}"
    print(f"  [OK] Planner Decision Influenced: '{planner_step.decision[:100]}...'")
    print("  [OK] Coder Patch Applied Fallback.")
    print(f"  [OK] Run 2 Status: {result_run2.status}")

    print("\n=================================================================")
    print(" ALL CLOSED-LOOP MEMORY ACCEPTANCE CRITERIA PASSED 100%!          ")
    print("=================================================================\n")

if __name__ == "__main__":
    test_complete_closed_loop_memory_cycle()
