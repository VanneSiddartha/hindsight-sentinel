import os
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.models.experience import ExperienceModel
from app.experience.retain import LOCAL_EXPERIENCE_VAULT, get_hindsight_client

load_dotenv()

logger = logging.getLogger(__name__)

def build_workflow_recall_query(context: WorkflowContext) -> str:
    return (
        f"Workflow type: {context.workflow_type}. "
        f"Service: {context.service_name}. Version: {context.version}. "
        f"Repository/project: {context.repository or 'not provided'}. "
        f"Environment: {context.environment}. Deployment target: {context.deployment_target or 'not provided'}. "
        f"Task: {context.task_description}"
    )

def recall_experiences_with_status(
    context_query: str,
    service_name: Optional[str] = None,
    top_k: int = 3,
) -> tuple[List[Dict[str, Any]], bool, Optional[str]]:
    """
    Recalls past relevant experiences from Hindsight vector memory using official hindsight-client SDK.
    Safe across sync and running asyncio event loops.
    """
    recalled_items: List[Dict[str, Any]] = []
    remote_available = False
    remote_error: Optional[str] = None
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    
    client = get_hindsight_client()
    if client:
        try:
            res = None
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # Synchronous execution wrapper in active loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(client.recall, bank_id=bank_id, query=context_query)
                        res = future.result(timeout=5.0)
                else:
                    res = client.recall(bank_id=bank_id, query=context_query)
            except RuntimeError:
                res = client.recall(bank_id=bank_id, query=context_query)

            if res and hasattr(res, "results") and res.results:
                for r in res.results:
                    meta = getattr(r, "metadata", {}) or {}
                    exp_id = meta.get("experience_id") if isinstance(meta, dict) else None
                    if not exp_id:
                        exp_id = getattr(r, "id", "remote-exp")
                    
                    text_content = getattr(r, "text", getattr(r, "content", ""))
                    lesson_text = meta.get("lesson") if isinstance(meta, dict) and meta.get("lesson") else text_content
                    outcome_val = meta.get("outcome") if isinstance(meta, dict) and meta.get("outcome") else "UNKNOWN"
                    score_value = getattr(r, "score", None)
                    if score_value is None:
                        score_value = getattr(getattr(r, "scores", None), "final", None)
                    try:
                        score = float(score_value) if score_value is not None else None
                    except (TypeError, ValueError):
                        score = None
                    
                    recalled_items.append({
                        "experience_id": exp_id,
                        "context": text_content,
                        "service_name": meta.get("service_name") if isinstance(meta, dict) else None,
                        "outcome": outcome_val,
                        "lesson": lesson_text,
                        "score": score,
                        "tags": getattr(r, "tags", None) or (
                            meta.get("tags", []) if isinstance(meta, dict) else []
                        )
                    })
            remote_available = True
            logger.info("Hindsight recall completed; returned %s remote memories.", len(recalled_items))
        except Exception as e:
            remote_error = str(e)
            logger.warning("Hindsight remote recall failed; trying local memory fallback: %s", e)
    else:
        remote_error = "Remote Hindsight is not configured."

    # Fallback / Complement with local vault semantic search matching
    if not recalled_items:
        def terms(value: str) -> set[str]:
            stop_words = {
                "workflow", "type", "service", "version", "repository", "project",
                "environment", "target", "task", "the", "for", "with", "from",
                "and", "deploy", "deployment", "a", "to", "in", "on", "is",
                "not", "provided", "of",
            }
            aliases = {
                "database": "db",
                "databases": "db",
                "migrate": "migration",
                "migrating": "migration",
                "authentication": "auth",
                "kubernetes": "k8s",
                "configuration": "config",
                "configurations": "config",
            }
            return {
                aliases.get(token, token)
                for token in re.findall(r"[a-z0-9]+", value.lower())
                if token not in stop_words
            }

        query_words = terms(context_query)
        for exp_id, exp in LOCAL_EXPERIENCE_VAULT.items():
            exp_text = f"{exp.context} {exp.service_name} {' '.join(exp.tags)} {exp.lesson} {exp.future_applicability}".lower()
            exp_words = terms(exp_text)
            overlap = query_words.intersection(exp_words)

            score = len(overlap) / max(min(len(query_words), len(exp_words), 8), 1)
            if service_name and service_name.lower() == exp.service_name.lower():
                score += 0.15

            for phrase in ["legacy auth", "auth middleware", "flaky test", "env variable", "misconfig", "race condition"]:
                if phrase in context_query.lower() and phrase in exp_text:
                    score += 0.45
            
            if score > 0.3:
                recalled_items.append({
                    "experience_id": exp.experience_id,
                    "context": exp.context,
                    "service_name": exp.service_name,
                    "outcome": exp.outcome,
                    "lesson": exp.lesson,
                    "root_cause": exp.root_cause,
                    "future_applicability": exp.future_applicability,
                    "score": round(min(score, 1.0), 2),
                    "tags": exp.tags
                })
                
    recalled_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    message = None
    if not remote_available:
        if recalled_items:
            message = "Remote Hindsight is unavailable; relevant local experiences were used."
        else:
            message = "Hindsight memory service is unavailable; continuing without historical memory."
    elif remote_error:
        message = "Remote Hindsight is unavailable; local experiences were used where relevant."
    return recalled_items[:top_k], remote_available, message

def recall_experiences(context_query: str, service_name: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
    recalled, _, _ = recall_experiences_with_status(context_query, service_name, top_k)
    return recalled
