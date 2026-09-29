from app.risk.risk_engine import evaluate_risk_rule
from app.models.experience import ExperienceModel
from app.experience.retain import retain_experience

def test_risk_engine_rules():
    # 1. Test NORMAL state
    risk_level, evidence, rec_action = evaluate_risk_rule([])
    assert risk_level == "NORMAL"
    assert len(evidence) == 0
    assert rec_action == "No known risk detected."
    
    # Seed a past failure experience
    exp = ExperienceModel(
        experience_id="exp-incident-99",
        context="Flaky async worker test suite failure in production build",
        service_name="async-worker",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Omitted retry timeout handling in worker queue",
        action="Merged patch without retry handler",
        validation="Production outage during peak load spike",
        outcome="FAILURE",
        root_cause="Missing timeout retry in worker connection",
        lesson="Always enforce 300ms exponential retry policy on async worker pools",
        future_applicability="Async queue deployments",
        tags=["flaky test", "async worker"]
    )
    retain_experience(exp)
    
    # 2. Test HIGH RISK state on past failure match
    recalled_mock = [{
        "experience_id": exp.experience_id,
        "context": exp.context,
        "outcome": exp.outcome,
        "score": 0.92,
        "lesson": exp.lesson
    }]
    
    risk_level_high, evidence_high, rec_action_high = evaluate_risk_rule(recalled_mock)
    assert risk_level_high == "HIGH RISK"
    assert len(evidence_high) == 1
    assert "exp-incident-99" in evidence_high[0]["experience_id"]
    assert "HIGH RISK DETECTED" in rec_action_high
    
    print("Step 4 Risk Engine Test Passed! Normal phrase & High Risk verified.")

if __name__ == "__main__":
    test_risk_engine_rules()
