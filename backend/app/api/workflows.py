from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Dict, List, Literal, Optional
from app.models.experience import WorkflowContext
from app.agents.pipeline import execute_agent_pipeline

router = APIRouter(prefix="/workflows", tags=["workflows"])

WORKFLOW_DB: Dict[str, WorkflowContext] = {}

class RunWorkflowRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "workflow_type": "deployment",
                "task_description": "Deploy the new payment service version",
                "service_name": "payment-service",
                "version": "v2.5.0",
                "repository": "payment-service-demo",
                "environment": "production",
                "deployment_target": "kubernetes",
            }]
        }
    )

    workflow_type: Literal[
        "deployment",
        "database_migration",
        "configuration_change",
        "service_update",
    ] = Field(description="Kind of controlled workflow analysis.")
    task_description: str = Field(
        min_length=1,
        description="Natural-language description. This is analyzed, not executed as a shell command.",
    )
    service_name: str = Field(min_length=1, description="Service or component being changed.")
    version: str = Field(min_length=1, description="Version or release identifier.")
    repository: Optional[str] = Field(default="payment-service-demo", description="Repository/project label; no code is fetched.")
    environment: Literal["development", "staging", "production"] = Field(
        description="Target environment."
    )
    deployment_target: Literal["kubernetes", "docker", "cloud_vm", "other"] = Field(
        default="kubernetes",
        description="Intended deployment target; no real deployment is performed.",
    )

    @field_validator("workflow_type", mode="before")
    @classmethod
    def normalize_workflow_type(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower().replace(" ", "_").replace("-", "_")
        return value

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("deployment_target", mode="before")
    @classmethod
    def normalize_deployment_target(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower().replace(" ", "_").replace("-", "_")
        return value

    @field_validator("repository", mode="before")
    @classmethod
    def normalize_repository(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or "payment-service-demo"
        return value

    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Service name is required.")
        return value

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Version is required.")
        return value

    @field_validator("task_description")
    @classmethod
    def validate_task_description(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Task description is required.")
        return value

@router.post("/run", response_model=WorkflowContext)
def run_workflow(
    req: RunWorkflowRequest,
    force_failure: bool = Query(
        default=False,
        include_in_schema=False,
        description="Internal replay-demo control; not for normal workflow requests.",
    ),
    enable_recall: bool = Query(
        default=True,
        include_in_schema=False,
        description="Internal replay-demo control; not for normal workflow requests.",
    ),
):
    context = WorkflowContext(
        task_description=req.task_description,
        service_name=req.service_name,
        workflow_type=req.workflow_type,
        version=req.version,
        repository=req.repository,
        environment=req.environment,
        deployment_target=req.deployment_target,
    )
    
    # Execute 4-agent pipeline with risk engine
    execute_agent_pipeline(context, force_failure=force_failure, enable_recall=enable_recall)
    
    # Store workflow record
    WORKFLOW_DB[context.workflow_id] = context
    return context

@router.get("/{workflow_id}", response_model=WorkflowContext)
def get_workflow(workflow_id: str):
    if workflow_id not in WORKFLOW_DB:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WORKFLOW_DB[workflow_id]

@router.get("", response_model=List[WorkflowContext])
@router.get("/", response_model=List[WorkflowContext])
def list_workflows():
    return list(WORKFLOW_DB.values())
