import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.main import app
from app.models.experience import WorkflowContext, WorkflowEvidence
from app.api import workflows
from app.agents import pipeline
from app.experience import retain
from app.experience import recall as recall_module
from app.risk.risk_engine import assess_workflow_risk


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setenv("HINDSIGHT_API_KEY", "")
    monkeypatch.setattr("app.main.seed_hindsight_experiences", lambda: 0)
    with TestClient(app) as client:
        yield client


def valid_request():
    return {
        "workflow_type": "Deployment",
        "task_description": "Deploy the new payment service version",
        "service_name": " payment-service ",
        "version": " v2.5.0 ",
        "repository": "payment-service-demo",
        "environment": "Production",
        "deployment_target": "Cloud VM",
    }


def test_valid_workflow_normalizes_context_and_returns_rich_response(api_client, monkeypatch):
    def stub_pipeline(context, force_failure=False, enable_recall=True):
        context.status = "COMPLETED_WITH_WARNING"
        context.outcome = "ANALYZED"
        return context

    monkeypatch.setattr(workflows, "execute_agent_pipeline", stub_pipeline)
    response = api_client.post("/workflows/run", json=valid_request())

    assert response.status_code == 200
    body = response.json()
    assert body["workflow_type"] == "deployment"
    assert body["service_name"] == "payment-service"
    assert body["version"] == "v2.5.0"
    assert body["environment"] == "production"
    assert body["deployment_target"] == "cloud_vm"
    assert body["repository"] == "payment-service-demo"
    assert body["outcome"] == "ANALYZED"
    assert body["llm"]["provider"] == "gemini"
    assert body["llm"]["used"] is False
    assert body["gemini_reasoning"] == []
    assert "GEMINI_API_KEY" not in response.text


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("service_name", None, "Service name is required."),
        ("version", None, "Version is required."),
        ("environment", "qa", "Environment must be development, staging, or production."),
        ("workflow_type", "release", "Workflow type is invalid or missing."),
    ],
)
def test_invalid_workflow_context_has_clear_validation_error(api_client, field, value, message):
    payload = valid_request()
    if value is None:
        payload.pop(field)
    else:
        payload[field] = value

    response = api_client.post("/workflows/run", json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == "workflow_validation_error"
    assert response.json()["message"] == message


def test_workflow_type_environment_and_target_are_normalized(api_client, monkeypatch):
    monkeypatch.setattr(
        workflows,
        "execute_agent_pipeline",
        lambda context, **kwargs: context,
    )
    payload = valid_request()
    payload["workflow_type"] = "DATABASE MIGRATION"
    payload["environment"] = "STAGING"
    payload["deployment_target"] = "Kubernetes"

    body = api_client.post("/workflows/run", json=payload).json()
    assert body["workflow_type"] == "database_migration"
    assert body["environment"] == "staging"
    assert body["deployment_target"] == "kubernetes"


def test_openapi_shows_workflow_form_fields_but_hides_demo_controls(api_client):
    schema = api_client.get("/openapi.json").json()
    request_schema = schema["components"]["schemas"]["RunWorkflowRequest"]
    assert set(request_schema["required"]) >= {
        "workflow_type",
        "task_description",
        "service_name",
        "version",
        "environment",
    }
    assert "repository" in request_schema["properties"]
    assert "deployment_target" in request_schema["properties"]
    run_operation = schema["paths"]["/workflows/run"]["post"]
    assert not any(
        parameter["name"] in {"force_failure", "enable_recall"}
        for parameter in run_operation.get("parameters", [])
    )


def test_risk_engine_combines_current_and_historical_evidence():
    normal = assess_workflow_risk([])
    assert normal[0] == "NORMAL"

    weak_historical_match = [{
        "experience_id": "exp-weak",
        "context": "Related service update",
        "outcome": "FAILURE",
        "score": 0.4,
        "lesson": "Review the configuration.",
    }]
    caution = assess_workflow_risk(weak_historical_match)
    assert caution[0] == "CAUTION"
    assert caution[1][0].source == "historical"

    strong_historical_match = [{
        "experience_id": "exp-strong",
        "context": "Matching production auth migration",
        "outcome": "FAILURE",
        "score": 0.92,
        "lesson": "Preserve the fallback.",
    }]
    assert assess_workflow_risk(strong_historical_match)[0] == "HIGH RISK"

    current_failure = [WorkflowEvidence(
        source="current",
        description="Validation failed.",
        severity="high",
    )]
    current_risk = assess_workflow_risk([], current_failure)
    assert current_risk[0] == "HIGH RISK"
    assert current_risk[1] == []


def test_relevant_hindsight_memory_changes_agent_decisions(monkeypatch):
    recalled = [{
        "experience_id": "exp-auth",
        "context": "API v2 release with legacy auth middleware",
        "service_name": "payment-auth",
        "outcome": "FAILURE",
        "lesson": "Preserve X-Legacy-Auth fallback.",
        "score": 0.95,
    }]
    monkeypatch.setattr(pipeline, "recall_experiences_with_status", lambda *args, **kwargs: (recalled, False, "Local vault memory."))
    monkeypatch.setattr(pipeline, "explain_experience_relevance", lambda *args: "Historical fallback lesson is relevant.")
    monkeypatch.setattr(pipeline, "extract_experience_from_workflow", lambda context: None)
    context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy API v2 endpoint with legacy auth middleware",
        service_name="payment-auth",
        version="v2",
        environment="production",
    )

    result = pipeline.execute_agent_pipeline(context)
    assert result.recalled_experiences == recalled
    assert result.hindsight_reflection == "Historical fallback lesson is relevant."
    assert result.risk_level == "HIGH RISK"
    assert result.status == "BLOCKED_BY_RISK"
    assert result.steps[0].metadata["memory_influenced"] is True
    assert result.steps[1].metadata["memory_influenced"] is True
    assert result.steps[2].status == "SUCCESS"


def test_hindsight_unavailable_degrades_without_claiming_memory(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "recall_experiences_with_status",
        lambda *args, **kwargs: ([], False, "Hindsight memory service is unavailable; continuing without historical memory."),
    )
    monkeypatch.setattr(pipeline, "explain_experience_relevance", lambda *args: None)
    monkeypatch.setattr(pipeline, "extract_experience_from_workflow", lambda context: None)
    context = WorkflowContext(
        workflow_type="service_update",
        task_description="Update a service",
        service_name="catalog-service",
        version="v3",
        environment="development",
    )

    result = pipeline.execute_agent_pipeline(context)
    assert result.status == "COMPLETED_WITH_WARNING"
    assert not result.hindsight_available
    assert result.recalled_experiences == []
    assert "unavailable" in result.hindsight_message.lower()
    assert result.extracted_experience is None


def test_remote_recall_uses_sdk_scores_and_tags_without_defaults(monkeypatch):
    recalled_result = SimpleNamespace(
        id="remote-exp-1",
        text="A production database migration used a blocking index build.",
        metadata={
            "experience_id": "remote-exp-1",
            "service_name": "orders",
            "outcome": "FAILURE",
            "lesson": "Use concurrent index creation.",
        },
        scores=SimpleNamespace(final=0.88),
        tags=["database", "migration"],
    )
    fake_client = SimpleNamespace(
        recall=lambda **kwargs: SimpleNamespace(results=[recalled_result]),
    )
    monkeypatch.setenv("HINDSIGHT_BANK_ID", "test-bank")
    monkeypatch.setattr(recall_module, "get_hindsight_client", lambda: fake_client)

    recalled, remote_available, message = recall_module.recall_experiences_with_status(
        "production database migration for orders",
        service_name="orders",
    )

    assert remote_available
    assert message is None
    assert recalled[0]["experience_id"] == "remote-exp-1"
    assert recalled[0]["score"] == 0.88
    assert recalled[0]["tags"] == ["database", "migration"]


def test_experience_retention_reports_local_only_without_hindsight(monkeypatch):
    monkeypatch.setattr(retain, "get_hindsight_client", lambda: None)
    retain.LOCAL_EXPERIENCE_VAULT.clear()
    monkeypatch.setattr(pipeline, "recall_experiences_with_status", lambda *args, **kwargs: ([], False, "Hindsight is unavailable."))
    monkeypatch.setattr(pipeline, "explain_experience_relevance", lambda *args: None)
    context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy API v2 endpoint with legacy auth middleware",
        service_name="payment-auth",
        version="v2",
        environment="staging",
    )

    result = pipeline.execute_agent_pipeline(context, force_failure=True, enable_recall=False)
    assert result.extracted_experience is not None
    assert result.retention_status == "local_only"
    assert not result.hindsight_available
    assert result.extracted_experience.experience_id in retain.LOCAL_EXPERIENCE_VAULT
    assert "local vault only" in result.hindsight_message.lower()
