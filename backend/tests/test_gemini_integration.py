import json
from types import SimpleNamespace

from app.agents import pipeline
from app.llm import gemini_client
from app.models.experience import WorkflowContext


def valid_gemini_json():
    return json.dumps({
        "summary": "Review the deployment context and validate the historical lesson.",
        "observations": ["The target environment is production."],
        "historical_context": ["A retained deployment lesson is relevant."],
        "concerns": ["Configuration should be checked before a real deployment."],
        "recommended_action": "Review the configuration evidence.",
    })


def test_gemini_client_initialization_is_lazy_and_cached(monkeypatch):
    created = []
    fake_client = object()
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setattr(
        gemini_client,
        "_create_client",
        lambda api_key: created.append(api_key) or fake_client,
    )
    gemini_client._client = None

    assert gemini_client.get_client() is fake_client
    assert gemini_client.get_client() is fake_client
    assert created == ["test-only-key"]


def test_missing_gemini_api_key_falls_back_without_claiming_usage(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy service",
        service_name="payment-service",
        version="v2",
        environment="staging",
    )

    assert gemini_client.analyze_workflow_agent(context, "planner", "Plan") is None
    assert context.llm.used is False
    assert context.llm.status == "not_configured"
    assert context.llm.agents_used == []


def test_successful_gemini_call_returns_structured_reasoning_with_hindsight(monkeypatch):
    prompts = []
    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: (
                prompts.append(kwargs)
                or SimpleNamespace(text=valid_gemini_json())
            )
        )
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(gemini_client, "_client", fake_client)
    context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy the payment service",
        service_name="payment-service",
        version="v2.5.0",
        environment="production",
        recalled_experiences=[{
            "experience_id": "exp-test",
            "context": "Earlier production config mismatch",
            "outcome": "FAILURE",
            "lesson": "Validate environment-specific configuration.",
        }],
    )

    result = gemini_client.analyze_workflow_agent(
        context,
        "planner",
        "Interpret the plan.",
        {"plan": ["validate config"]},
    )

    assert result is not None
    assert result.agent_name == "planner"
    assert result.summary.startswith("Review the deployment")
    assert context.llm.used is True
    assert context.llm.status == "used"
    assert context.llm.agents_used == ["planner"]
    prompt = prompts[0]["contents"]
    assert "exp-test" in prompt
    assert "Validate environment-specific configuration." in prompt
    assert prompts[0]["model"] == "test-model"


def test_gemini_api_failure_and_invalid_output_return_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy service",
        service_name="service",
        version="v1",
        environment="development",
    )

    failing_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("provider failure")))
    )
    monkeypatch.setattr(gemini_client, "_client", failing_client)
    assert gemini_client.analyze_workflow_agent(context, "coder", "Review") is None
    assert context.llm.status == "error"
    assert context.llm.used is False

    invalid_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text="not json"))
    )
    monkeypatch.setattr(gemini_client, "_client", invalid_client)
    invalid_context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy service",
        service_name="service",
        version="v1",
        environment="development",
    )
    assert gemini_client.analyze_workflow_agent(invalid_context, "coder", "Review") is None
    assert invalid_context.llm.status == "invalid_response"
    assert invalid_context.llm.used is False


def test_agent_pipeline_uses_gemini_with_recalled_memories_and_keeps_risk_deterministic(monkeypatch):
    recalled = [{
        "experience_id": "exp-memory",
        "context": "Production auth fallback incident",
        "service_name": "payment-auth",
        "outcome": "FAILURE",
        "lesson": "Preserve the existing auth fallback.",
        "score": 0.95,
    }]
    prompts = []
    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: (
                prompts.append(kwargs["contents"])
                or SimpleNamespace(text=valid_gemini_json())
            )
        )
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setattr(gemini_client, "_client", fake_client)
    monkeypatch.setattr(
        pipeline,
        "recall_experiences_with_status",
        lambda *args, **kwargs: (recalled, True, None),
    )
    monkeypatch.setattr(
        pipeline,
        "explain_experience_relevance",
        lambda *args: "Prior auth fallback experience was recalled.",
    )
    monkeypatch.setattr(pipeline, "extract_experience_from_workflow", lambda context: None)
    context = WorkflowContext(
        workflow_type="deployment",
        task_description="Deploy API v2 endpoint with legacy auth middleware",
        service_name="payment-auth",
        version="v2",
        environment="production",
    )

    result = pipeline.execute_agent_pipeline(context)

    assert result.llm.used is True
    assert result.llm.status == "used"
    assert result.llm.agents_used == ["planner", "coder", "tester", "security"]
    assert [item.agent_name for item in result.gemini_reasoning] == [
        "planner",
        "coder",
        "tester",
        "security",
    ]
    assert all("Preserve the existing auth fallback." in prompt for prompt in prompts)
    assert result.risk_level == "HIGH RISK"
    assert result.status == "BLOCKED_BY_RISK"
    assert result.steps[2].status == "SUCCESS"


def test_pipeline_runs_deterministically_when_gemini_is_not_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setattr(
        pipeline,
        "recall_experiences_with_status",
        lambda *args, **kwargs: ([], False, "Hindsight unavailable."),
    )
    monkeypatch.setattr(pipeline, "explain_experience_relevance", lambda *args: None)
    monkeypatch.setattr(pipeline, "extract_experience_from_workflow", lambda context: None)
    context = WorkflowContext(
        workflow_type="service_update",
        task_description="Update service",
        service_name="catalog-service",
        version="v3",
        environment="development",
    )

    result = pipeline.execute_agent_pipeline(context)

    assert result.llm.provider == "gemini"
    assert result.llm.used is False
    assert result.llm.status == "not_configured"
    assert result.gemini_reasoning == []
    assert [step.agent_name for step in result.steps] == [
        "planner",
        "coder",
        "tester",
        "security",
    ]
