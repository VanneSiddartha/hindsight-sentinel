import pytest

from app.experience import recall, reflect, retain
from app.llm import gemini_client


@pytest.fixture(autouse=True)
def disable_external_services(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("HINDSIGHT_API_KEY", "")
    monkeypatch.setenv("HINDSIGHT_EXPERIENCE_DB_PATH", str(tmp_path / "experiences.sqlite3"))
    monkeypatch.setattr(retain, "get_hindsight_client", lambda: None)
    monkeypatch.setattr(gemini_client, "_client", None)
    monkeypatch.setattr(recall, "get_hindsight_client", lambda: None)
    monkeypatch.setattr(reflect, "get_hindsight_client", lambda: None)
    retain.LOCAL_EXPERIENCE_VAULT.clear()
