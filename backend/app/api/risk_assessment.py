from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.experience.recall import recall_experiences
from app.experience.reflect import reflect_on_experience

router = APIRouter(prefix="/risk-assessment", tags=["risk-assessment"])

class RiskAssessmentRequest(BaseModel):
    task_description: str
    service_name: Optional[str] = None
    environment: str = "production"

class RiskAssessmentResponse(BaseModel):
    risk_level: str  # "NORMAL", "CAUTION", "HIGH RISK"
    evidence: List[Dict[str, Any]]
    recommended_action: str
    recalled_experiences: List[Dict[str, Any]]

@router.post("", response_model=RiskAssessmentResponse)
@router.post("/", response_model=RiskAssessmentResponse)
def assess_risk(req: RiskAssessmentRequest):
    recalled = recall_experiences(req.task_description, service_name=req.service_name)
    risk_level, evidence, recommended_action = reflect_on_experience(req.task_description, recalled)
    
    return RiskAssessmentResponse(
        risk_level=risk_level,
        evidence=evidence,
        recommended_action=recommended_action,
        recalled_experiences=recalled
    )
