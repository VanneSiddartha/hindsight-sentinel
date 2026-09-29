from app.models.experience import ExperienceModel
from app.experience.retain import retain_experience, LOCAL_EXPERIENCE_VAULT
from app.experience.recall import recall_experiences
from app.experience.reflect import reflect_on_experience

def test_retain_recall_reflect():
    # 1. Test Retain
    exp = ExperienceModel(
        experience_id="exp-test-01",
        context="API v2 release with legacy auth middleware",
        service_name="payment-auth",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Attempted to strip legacy headers in API v2 route",
        action="Applied code patch omitting legacy auth headers",
        validation="Integration tests failed with 401 Unauthorized",
        outcome="FAILURE",
        root_cause="Legacy authorization header required by existing web clients",
        lesson="Always preserve X-Legacy-Auth header fallback when upgrading API v2",
        future_applicability="API route migrations involving authentication",
        tags=["legacy auth", "auth middleware", "api v2"]
    )
    
    retain_res = retain_experience(exp)
    assert retain_res["status"] == "retained"
    assert exp.experience_id in LOCAL_EXPERIENCE_VAULT
    
    # 2. Test Recall
    recalled = recall_experiences("Deploy API v2 endpoint with legacy auth middleware", service_name="payment-auth")
    assert len(recalled) > 0
    assert recalled[0]["outcome"] == "FAILURE"
    assert "legacy" in recalled[0]["lesson"].lower()
    
    # 3. Test Reflect
    risk_level, evidence, rec_action = reflect_on_experience("Deploy API v2 endpoint with legacy auth middleware", recalled)
    assert risk_level in ["CAUTION", "HIGH RISK"]
    assert len(evidence) > 0
    assert "high risk" in rec_action.lower() or "legacy" in rec_action.lower()
    
    print("Step 3 Hindsight Experience Test Passed! Risk level:", risk_level)

if __name__ == "__main__":
    test_retain_recall_reflect()
