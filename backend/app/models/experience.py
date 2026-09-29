from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_name: str  # "planner", "coder", "tester", "security"
    timestamp: str = Field(default_factory=current_utc_iso)
    observation: str
    decision: str
    action_taken: str
    status: str  # "SUCCESS", "FAILED", "WARNING", "SKIPPED"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExperienceAgentActivity(BaseModel):
    agent_name: str
    decision: str
    action: str
    status: str

class WorkflowEvidence(BaseModel):
    source: Literal["current", "historical"]
    description: str
    severity: Literal["info", "caution", "high"]
    experience_id: Optional[str] = None
    context: Optional[str] = None
    outcome: Optional[str] = None
    score: Optional[float] = None
    reason: Optional[str] = None

class GeminiAgentReasoning(BaseModel):
    agent_name: Literal["planner", "coder", "tester", "security"]
    summary: str
    observations: List[str] = Field(default_factory=list)
    historical_context: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None

class LLMStatus(BaseModel):
    provider: Literal["gemini"] = "gemini"
    model: str
    used: bool = False
    status: Literal["not_configured", "ready", "used", "error", "invalid_response"] = "not_configured"
    agents_used: List[str] = Field(default_factory=list)

class ExperienceModel(BaseModel):
    experience_id: str = Field(default_factory=lambda: f"exp-{uuid.uuid4().hex[:8]}")
    context: str  # Task description / context tags
    service_name: str
    agents_involved: List[str]
    decision: str
    action: str
    validation: str
    outcome: str  # "SUCCESS" or "FAILURE"
    root_cause: Optional[str] = None
    lesson: str
    future_applicability: str
    workflow_id: Optional[str] = None
    workflow_type: Optional[str] = None
    task_description: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    agent_activities: List[ExperienceAgentActivity] = Field(default_factory=list)
    timestamp: str = Field(default_factory=current_utc_iso)
    tags: List[str] = Field(default_factory=list)
    source: str = "workflow"
    metadata_status: str = "not_saved"
    hindsight_status: str = "not_attempted"

class WorkflowContext(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    task_description: str
    service_name: str
    workflow_type: str = "deployment"
    version: str = "unknown"
    repository: Optional[str] = None
    environment: str = "production"
    deployment_target: Optional[str] = "kubernetes"
    created_at: str = Field(default_factory=current_utc_iso)
    status: str = "PENDING"  # PENDING, IN_PROGRESS, PASSED, FAILED, BLOCKED_BY_RISK, COMPLETED_WITH_WARNING
    outcome: Optional[str] = None
    risk_level: Optional[str] = "NORMAL"  # "NORMAL", "CAUTION", "HIGH RISK"
    current_evidence: List[WorkflowEvidence] = Field(default_factory=list)
    risk_evidence: List[WorkflowEvidence] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    recalled_experiences: List[Dict[str, Any]] = Field(default_factory=list)
    hindsight_available: bool = False
    hindsight_message: Optional[str] = None
    hindsight_reflection: Optional[str] = None
    retention_status: str = "not_attempted"
    metadata_status: str = "not_saved"
    hindsight_retention_status: str = "not_attempted"
    summary_lesson: Optional[str] = None
    steps: List[AgentStep] = Field(default_factory=list)
    extracted_experience: Optional[ExperienceModel] = None
    llm: LLMStatus = Field(default_factory=lambda: LLMStatus(model="gemini-2.5-flash"))
    gemini_reasoning: List[GeminiAgentReasoning] = Field(default_factory=list)
