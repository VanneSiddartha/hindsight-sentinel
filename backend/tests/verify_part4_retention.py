import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.experience import ExperienceModel
from app.experience.retain import retain_experience, get_hindsight_client

def run_part4_retention_test():
    print("=== PART 4: VERIFY HINDSIGHT RETENTION ===")
    client = get_hindsight_client()
    print(f"Hindsight SDK Client Loaded? {client is not None}")
    
    exp = ExperienceModel(
        experience_id="exp-part4-test",
        context="Test database connection error retention",
        service_name="db-service",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Attempted connection without SSL certificates",
        action="Applied unencrypted DB pool patch",
        validation="FAIL: SSLConnectionError",
        outcome="FAILURE",
        root_cause="Missing SSL certificate configuration",
        lesson="Always enforce TLS/SSL certificate validation on production DB pools",
        future_applicability="Database connection security",
        tags=["db", "ssl", "test"],
        source="agent_run"
    )
    
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    print(f"Bank ID Target: {bank_id}")
    
    if client:
        try:
            res = client.retain(
                bank_id=bank_id,
                content=f"Context: {exp.context}. Lesson: {exp.lesson}.",
                document_id=exp.experience_id,
                metadata={"experience_id": exp.experience_id, "source": exp.source},
                tags=exp.tags
            )
            print(f"Remote Hindsight SDK client.retain() Call Succeeded! Response: {res}")
        except Exception as e:
            print(f"Remote Hindsight SDK client.retain() Exception: {e}")
            
    res_dict = retain_experience(exp)
    print(f"retain_experience() Result Dict: {res_dict}")

if __name__ == "__main__":
    run_part4_retention_test()
