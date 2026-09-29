import os
import asyncio
import concurrent.futures
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from app.models.experience import ExperienceModel

load_dotenv()
logger = logging.getLogger(__name__)

# Local persistent vault fallback / cache
LOCAL_EXPERIENCE_VAULT: Dict[str, ExperienceModel] = {}

def get_hindsight_client():
    """
    Returns an instance of the official Vectorize Hindsight SDK client (hindsight-client).
    Uses environment variables for credentials.
    """
    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    
    if not api_key:
        return None
        
    try:
        from hindsight_client import Hindsight
        return Hindsight(base_url=base_url, api_key=api_key)
    except Exception as e:
        logger.warning("Could not initialize the Hindsight client: %s", e)
        return None

def retain_experience(experience: ExperienceModel) -> Dict[str, Any]:
    """
    Retains a completed experience memory into Hindsight using official hindsight-client SDK.
    Handles both synchronous and active asyncio event loops safely.
    """
    LOCAL_EXPERIENCE_VAULT[experience.experience_id] = experience
    
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    retained_remote = False
    message = None
    
    client = get_hindsight_client()
    if client:
        try:
            content_str = (
                f"Context: {experience.context}. Service: {experience.service_name}. "
                f"Decision: {experience.decision}. Outcome: {experience.outcome}. "
                f"Lesson: {experience.lesson}. Root cause: {experience.root_cause or 'N/A'}. "
                f"Source: {experience.source}."
            )
            meta = {
                "experience_id": experience.experience_id,
                "service_name": experience.service_name,
                "outcome": experience.outcome,
                "lesson": experience.lesson,
                "future_applicability": experience.future_applicability,
                "source": experience.source
            }
            tags_list = experience.tags or ["sentinel"]
            
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                client.retain(bank_id=bank_id, content=content_str, document_id=experience.experience_id, metadata=meta, tags=tags_list)
                retained_remote = True
            else:
                def retain_async() -> None:
                    asyncio.run(client.aretain(
                        bank_id=bank_id,
                        content=content_str,
                        document_id=experience.experience_id,
                        metadata=meta,
                        tags=tags_list,
                    ))

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(retain_async).result(timeout=10)
                retained_remote = True

            logger.info("Retained experience %s remotely in Hindsight.", experience.experience_id)
        except Exception as e:
            logger.warning("Hindsight remote retention failed; experience remains in local vault: %s", e)
            retained_remote = False
            message = "Remote Hindsight retention failed; the experience is available in the local vault only."
    else:
        message = "Remote Hindsight is not configured; the experience is available in the local vault only."

    return {
        "status": "retained",
        "experience_id": experience.experience_id,
        "remote_synced": retained_remote,
        "message": message,
        "vault_total": len(LOCAL_EXPERIENCE_VAULT)
    }
