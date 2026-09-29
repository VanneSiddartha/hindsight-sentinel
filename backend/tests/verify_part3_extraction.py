import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline

def run_part3_extraction_test():
    print("=== PART 3: VERIFY EXPERIENCE EXTRACTION ===")
    task = "Deploy API v2 endpoint with legacy auth middleware"
    ctx = WorkflowContext(task_description=task, service_name="payment-auth")
    
    result = execute_agent_pipeline(ctx, force_failure=True, enable_recall=False)
    
    ext = result.extracted_experience
    print(f"Extracted Experience Created? {ext is not None}")
    if ext:
        print(f"  - experience_id: {ext.experience_id}")
        print(f"  - context: {ext.context}")
        print(f"  - service_name: {ext.service_name}")
        print(f"  - agents_involved: {ext.agents_involved}")
        print(f"  - decision: {ext.decision[:80]}...")
        print(f"  - action: {ext.action}")
        print(f"  - validation: {ext.validation[:80]}...")
        print(f"  - outcome: {ext.outcome}")
        print(f"  - root_cause: {ext.root_cause}")
        print(f"  - lesson: {ext.lesson}")
        print(f"  - future_applicability: {ext.future_applicability}")
        print(f"  - tags: {ext.tags}")
        print(f"  - source: {ext.source}")
        
        assert ext.source == "agent_run"
        assert ext.outcome == "FAILURE"
        print("PART 3 VERIFICATION SUCCESSFUL: ExperienceModel(source='agent_run') extracted correctly!")
        return ext

if __name__ == "__main__":
    run_part3_extraction_test()
