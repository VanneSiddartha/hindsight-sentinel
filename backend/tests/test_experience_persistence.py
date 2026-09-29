import logging

from fastapi.testclient import TestClient

from app.experience import retain
from app.experience.seed import SEED_EXPERIENCES
from app.main import app
from app.models.experience import ExperienceModel, WorkflowContext
from app.agents.pipeline import execute_agent_pipeline


def make_experience(experience_id="exp-retention-test"):
    return ExperienceModel(
        experience_id=experience_id,
        context="Service update for catalog",
        service_name="catalog",
        agents_involved=["planner", "coder", "tester", "security"],
        decision="Proceed with the proposed update.",
        action="Recorded the proposed code change.",
        validation="Repository tests were not run.",
        outcome="ANALYZED",
        lesson="Repository validation remains unverified.",
        future_applicability="Service updates for catalog",
        workflow_id="wf-retention-test",
        workflow_type="service_update",
        task_description="Update catalog service",
        version="v1",
        environment="staging",
        source="workflow",
    )


def test_normal_analysis_workflow_extracts_persistent_experience():
    context = WorkflowContext(
        workflow_type="service_update",
        task_description="Update catalog service with the scheduled release",
        service_name="catalog",
        version="v4",
        environment="staging",
    )

    result = execute_agent_pipeline(context)

    assert result.outcome == "ANALYZED"
    assert result.steps[2].status == "WARNING"
    assert result.extracted_experience is not None
    experience = result.extracted_experience
    assert experience.outcome == "ANALYZED"
    assert experience.workflow_id == result.workflow_id
    assert experience.experience_id == f"exp-{result.workflow_id}"
    assert experience.source == "workflow"
    assert experience.validation == result.steps[2].metadata["test_output"]
    assert [activity.agent_name for activity in experience.agent_activities] == [
        "planner",
        "coder",
        "tester",
        "security",
    ]
    assert result.metadata_status == "persisted"
    assert result.hindsight_retention_status == "not_configured"
    assert retain.get_stored_experience(experience.experience_id) == experience


def test_hindsight_retain_is_called_and_success_is_reported(monkeypatch):
    calls = []

    class FakeHindsight:
        def retain(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setenv("HINDSIGHT_API_KEY", "test-key")
    monkeypatch.setenv("HINDSIGHT_BANK_ID", "test-bank")
    monkeypatch.setattr(retain, "get_hindsight_client", lambda: FakeHindsight())

    experience = make_experience()
    result = retain.retain_experience(experience)

    assert len(calls) == 1
    assert result["created"] is True
    assert calls[0]["bank_id"] == "test-bank"
    assert calls[0]["document_id"] == experience.experience_id
    assert calls[0]["metadata"]["workflow_id"] == experience.workflow_id
    assert result["metadata_saved"] is True
    assert result["remote_synced"] is True
    assert result["hindsight_status"] == "retained"
    assert experience.metadata_status == "persisted"
    assert experience.hindsight_status == "retained"
    duplicate = make_experience("exp-retention-retry")
    duplicate_result = retain.retain_experience(duplicate)
    assert duplicate_result["created"] is False
    assert duplicate_result["experience_id"] == experience.experience_id
    assert duplicate_result["remote_synced"] is True
    assert len(calls) == 1


def test_retain_deduplicates_same_workflow_and_preserves_distinct_workflows():
    experience = make_experience()
    first_result = retain.retain_experience(experience)

    retry = make_experience("exp-retention-retry")
    retry_result = retain.retain_experience(retry)

    assert first_result["created"] is True
    assert retry_result["created"] is False
    assert retry_result["experience_id"] == experience.experience_id
    assert retain.get_stored_experience(retry.experience_id) is None

    different_workflow = make_experience("exp-distinct-workflow")
    different_workflow.workflow_id = "wf-distinct"
    different_result = retain.retain_experience(different_workflow)

    stored = retain.list_stored_experiences()
    assert different_result["created"] is True
    assert len(stored) == 2
    assert {item.workflow_id for item in stored} == {"wf-retention-test", "wf-distinct"}


def test_history_api_deduplicates_legacy_workflow_rows_without_deleting_them():
    experiences = [
        make_experience("exp-legacy-workflow"),
        make_experience("exp-legacy-workflow-copy"),
        make_experience("exp-similar-distinct-workflow"),
    ]
    experiences[2].workflow_id = "wf-distinct"

    with retain._connect() as connection:
        for experience in experiences:
            experience.metadata_status = "persisted"
            connection.execute(
                """
                INSERT INTO experiences
                    (experience_id, payload, timestamp, source, workflow_id, metadata_status, hindsight_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experience.experience_id,
                    experience.model_dump_json(),
                    experience.timestamp,
                    experience.source,
                    experience.workflow_id,
                    experience.metadata_status,
                    experience.hindsight_status,
                ),
            )

    with TestClient(app) as client:
        history = client.get("/experiences").json()

    assert len(history) == 2
    assert {item["workflow_id"] for item in history} == {"wf-retention-test", "wf-distinct"}
    with retain._connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM experiences").fetchone()[0] == 3


def test_hindsight_failure_keeps_metadata_and_reports_failure(monkeypatch, caplog):
    secret = "test-hindsight-secret"

    class FakeHindsight:
        def retain(self, **kwargs):
            raise RuntimeError(f"remote error echoed {secret}")

    monkeypatch.setenv("HINDSIGHT_API_KEY", secret)
    monkeypatch.setattr(retain, "get_hindsight_client", lambda: FakeHindsight())
    experience = make_experience("exp-retention-failed")

    with caplog.at_level(logging.WARNING):
        result = retain.retain_experience(experience)

    assert result["metadata_saved"] is True
    assert result["remote_synced"] is False
    assert result["hindsight_status"] == "failed"
    assert "Hindsight retention did not complete" in result["message"]
    assert retain.get_stored_experience(experience.experience_id).hindsight_status == "failed"
    assert secret not in caplog.text


def test_history_api_keeps_workflow_and_explicit_demo_records_across_restart():
    with TestClient(app) as client:
        assert client.get("/experiences").json() == []
        assert client.get("/experiences").json() == []

        seed_response = client.post("/experiences/seed")
        assert seed_response.status_code == 200
        assert seed_response.json()["count"] == len(SEED_EXPERIENCES)
        assert client.post("/experiences/seed").json()["count"] == 0

        demo_records = client.get("/experiences").json()
        assert len(demo_records) == seed_response.json()["count"]
        assert {record["source"] for record in demo_records} == {"demo"}

        run_response = client.post(
            "/workflows/run",
            json={
                "workflow_type": "service_update",
                "task_description": "Update catalog service with the scheduled release",
                "service_name": "catalog",
                "version": "v5",
                "repository": "catalog",
                "environment": "staging",
                "deployment_target": "kubernetes",
            },
        )
        assert run_response.status_code == 200
        workflow_result = run_response.json()
        created = workflow_result["extracted_experience"]
        assert created["source"] == "workflow"
        assert created["workflow_id"] == workflow_result["workflow_id"]

        history_response = client.get("/experiences")
        assert history_response.status_code == 200
        first_history = history_response.json()
        assert created["experience_id"] in {record["experience_id"] for record in first_history}
        assert any(record["source"] == "demo" for record in first_history)
        workflow_records = [record for record in first_history if record["source"] == "workflow"]
        assert len(workflow_records) == 1
        assert len(first_history) == len(demo_records) + 1

        retry = ExperienceModel.model_validate(created).model_copy(
            update={"experience_id": f"{created['experience_id']}-retry"}
        )
        retry_result = retain.retain_experience(retry)
        assert retry_result["created"] is False
        assert retry_result["experience_id"] == created["experience_id"]

        assert client.get(f"/experiences/{created['experience_id']}").json() == created
        first_ids = [record["experience_id"] for record in first_history]
        assert len(first_ids) == len(set(first_ids))

    with TestClient(app) as restarted_client:
        second_history = restarted_client.get("/experiences").json()
        second_ids = [record["experience_id"] for record in second_history]
        assert created["experience_id"] in second_ids
        assert len(second_ids) == len(set(second_ids))
        assert len(restarted_client.get("/experiences").json()) == len(first_history)
        assert restarted_client.post("/experiences/seed").json()["count"] == 0
