import asyncio
import concurrent.futures
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from app.models.experience import ExperienceModel

load_dotenv()
logger = logging.getLogger(__name__)

LOCAL_EXPERIENCE_VAULT: Dict[str, ExperienceModel] = {}


def _database_path() -> Path:
    configured_path = os.getenv("HINDSIGHT_EXPERIENCE_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return Path(__file__).resolve().parents[3] / "data" / "experiences.sqlite3"


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS experiences (
            experience_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            workflow_id TEXT,
            metadata_status TEXT NOT NULL,
            hindsight_status TEXT NOT NULL
        )
        """
    )
    return connection


def get_stored_experience(experience_id: str) -> Optional[ExperienceModel]:
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM experiences WHERE experience_id = ?",
            (experience_id,),
        ).fetchone()
    if row is None:
        return None
    return ExperienceModel.model_validate_json(row["payload"])


def list_stored_experiences() -> List[ExperienceModel]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM experiences ORDER BY timestamp DESC, experience_id"
        ).fetchall()
    experiences: List[ExperienceModel] = []
    seen_workflow_ids = set()
    for row in rows:
        experience = ExperienceModel.model_validate_json(row["payload"])
        if experience.source in {"workflow", "agent_run"} and experience.workflow_id:
            if experience.workflow_id in seen_workflow_ids:
                logger.warning(
                    "Found duplicate workflow experiences for workflow_id=%s; returning one record.",
                    experience.workflow_id,
                )
                continue
            seen_workflow_ids.add(experience.workflow_id)
        experiences.append(experience)
    LOCAL_EXPERIENCE_VAULT.update(
        {experience.experience_id: experience for experience in experiences}
    )
    return experiences


def _save_experience(
    experience: ExperienceModel,
) -> tuple[bool, Optional[ExperienceModel]]:
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        existing_row = connection.execute(
            """
            SELECT payload FROM experiences
            WHERE experience_id = ?
            """,
            (experience.experience_id,),
        ).fetchone()
        if (
            existing_row is None
            and experience.source in {"workflow", "agent_run"}
            and experience.workflow_id
        ):
            existing_row = connection.execute(
                """
                SELECT payload FROM experiences
                WHERE workflow_id = ? AND source IN ('workflow', 'agent_run')
                ORDER BY timestamp DESC, experience_id
                LIMIT 1
                """,
                (experience.workflow_id,),
            ).fetchone()
        if existing_row is not None:
            return False, ExperienceModel.model_validate_json(existing_row["payload"])

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO experiences
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
        if cursor.rowcount != 1:
            existing_row = connection.execute(
                "SELECT payload FROM experiences WHERE experience_id = ?",
                (experience.experience_id,),
            ).fetchone()
            if existing_row is not None:
                return False, ExperienceModel.model_validate_json(existing_row["payload"])
    return True, None


def _already_retained_result(existing: ExperienceModel) -> Dict[str, Any]:
    LOCAL_EXPERIENCE_VAULT[existing.experience_id] = existing
    if existing.source in {"workflow", "agent_run"}:
        logger.info(
            "WORKFLOW EXPERIENCE workflow_id=%s experience_id=%s source=%s action=skipped reason=already_exists",
            existing.workflow_id,
            existing.experience_id,
            existing.source,
        )
    return {
        "status": "retained",
        "experience_id": existing.experience_id,
        "created": False,
        "metadata_saved": existing.metadata_status == "persisted",
        "metadata_status": existing.metadata_status,
        "remote_synced": existing.hindsight_status == "retained",
        "hindsight_status": existing.hindsight_status,
        "message": "This experience was already stored; no duplicate Hindsight retain was sent.",
        "vault_total": len(LOCAL_EXPERIENCE_VAULT),
    }


def _update_experience(experience: ExperienceModel) -> None:
    with _connect() as connection:
        connection.execute(
            """
            UPDATE experiences
            SET payload = ?, metadata_status = ?, hindsight_status = ?
            WHERE experience_id = ?
            """,
            (
                experience.model_dump_json(),
                experience.metadata_status,
                experience.hindsight_status,
                experience.experience_id,
            ),
        )


def _redact_api_key(error: Exception) -> str:
    message = str(error)
    api_key = os.getenv("HINDSIGHT_API_KEY")
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    return message


def get_hindsight_client():
    """Create the official Hindsight SDK client from the configured credentials."""
    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]

    if not api_key:
        return None

    try:
        from hindsight_client import Hindsight

        return Hindsight(base_url=base_url, api_key=api_key)
    except Exception as error:
        logger.warning("Could not initialize the Hindsight client: %s", _redact_api_key(error))
        return None


def retain_experience(experience: ExperienceModel) -> Dict[str, Any]:
    """Persist experience metadata locally and retain it in Hindsight when configured."""
    try:
        existing = get_stored_experience(experience.experience_id)
    except (OSError, sqlite3.Error) as error:
        existing = None
        logger.exception(
            "Could not check experience %s metadata: %s",
            experience.experience_id,
            error,
        )

    if existing is not None:
        return _already_retained_result(existing)

    experience.metadata_status = "persisted"
    experience.hindsight_status = "pending"
    metadata_saved = False
    try:
        metadata_saved, existing = _save_experience(experience)
        if existing is not None:
            return _already_retained_result(existing)
    except (OSError, sqlite3.Error) as error:
        experience.metadata_status = "temporary"
        logger.exception("Could not persist experience %s metadata: %s", experience.experience_id, error)

    LOCAL_EXPERIENCE_VAULT[experience.experience_id] = experience
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    retained_remote = False
    hindsight_status = "not_configured"
    message: Optional[str] = None

    client = get_hindsight_client()
    if client:
        try:
            content = (
                f"Workflow: {experience.workflow_id or 'not associated'} "
                f"({experience.workflow_type or 'type not recorded'}), "
                f"version {experience.version or 'not recorded'} in "
                f"{experience.environment or 'environment not recorded'}. "
                f"Task: {experience.task_description or experience.context}. "
                f"Context: {experience.context}. Service: {experience.service_name}. "
                f"Decision: {experience.decision}. Action: {experience.action}. "
                f"Validation: {experience.validation}. Outcome: {experience.outcome}. "
                f"Lesson: {experience.lesson}. Root cause: {experience.root_cause or 'not established'}. "
                f"Agent activities: "
                f"{'; '.join(f'{activity.agent_name}: {activity.decision} / {activity.action} ({activity.status})' for activity in experience.agent_activities)}. "
                f"Source: {experience.source}."
            )
            metadata = {
                "experience_id": experience.experience_id,
                "workflow_id": experience.workflow_id,
                "workflow_type": experience.workflow_type,
                "task_description": experience.task_description,
                "service_name": experience.service_name,
                "version": experience.version,
                "environment": experience.environment,
                "outcome": experience.outcome,
                "lesson": experience.lesson,
                "future_applicability": experience.future_applicability,
                "agents_involved": experience.agents_involved,
                "agent_activities": [
                    activity.model_dump() for activity in experience.agent_activities
                ],
                "source": experience.source,
            }
            tags = experience.tags or ["sentinel"]

            try:
                asyncio.get_running_loop()
            except RuntimeError:
                client.retain(
                    bank_id=bank_id,
                    content=content,
                    document_id=experience.experience_id,
                    metadata=metadata,
                    tags=tags,
                )
            else:
                def retain_async() -> None:
                    asyncio.run(
                        client.aretain(
                            bank_id=bank_id,
                            content=content,
                            document_id=experience.experience_id,
                            metadata=metadata,
                            tags=tags,
                        )
                    )

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(retain_async).result(timeout=10)

            retained_remote = True
            hindsight_status = "retained"
            logger.info("Retained experience %s remotely in Hindsight.", experience.experience_id)
        except Exception as error:
            hindsight_status = "failed"
            logger.error(
                "Hindsight remote retention failed for experience %s: %s",
                experience.experience_id,
                _redact_api_key(error),
            )
    elif os.getenv("HINDSIGHT_API_KEY"):
        hindsight_status = "failed"
        message = "Hindsight client initialization failed; remote retention was not completed."
    else:
        message = "Remote Hindsight is not configured."

    experience.hindsight_status = hindsight_status
    if metadata_saved:
        try:
            _update_experience(experience)
        except (OSError, sqlite3.Error) as error:
            logger.exception(
                "Could not update experience %s retention metadata: %s",
                experience.experience_id,
                error,
            )

    if not retained_remote:
        if metadata_saved:
            message = (
                "Experience metadata was saved locally, but Hindsight retention did not complete."
                if hindsight_status == "failed"
                else "Experience metadata was saved locally; remote Hindsight is not configured."
            )
        else:
            message = (
                "Experience is available in memory only; metadata persistence failed and Hindsight did not retain it."
            )
    elif not metadata_saved:
        message = "Hindsight retained the experience, but local metadata could not be persisted."

    created = metadata_saved or retained_remote
    if experience.source in {"workflow", "agent_run"}:
        logger.info(
            "WORKFLOW EXPERIENCE workflow_id=%s experience_id=%s source=%s action=%s reason=%s",
            experience.workflow_id,
            experience.experience_id,
            experience.source,
            "created" if created else "skipped",
            "workflow_completed" if created else "persistence_failed",
        )

    return {
        "status": "retained" if metadata_saved or retained_remote else "temporary",
        "experience_id": experience.experience_id,
        "created": created,
        "metadata_saved": metadata_saved,
        "metadata_status": experience.metadata_status,
        "remote_synced": retained_remote,
        "hindsight_status": hindsight_status,
        "message": message,
        "vault_total": len(LOCAL_EXPERIENCE_VAULT),
    }
