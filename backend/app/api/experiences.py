from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.experience import ExperienceModel
from app.experience.retain import retain_experience, LOCAL_EXPERIENCE_VAULT

router = APIRouter(prefix="/experiences", tags=["experiences"])

@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_experience(exp: ExperienceModel):
    result = retain_experience(exp)
    return result

@router.get("", response_model=List[ExperienceModel])
@router.get("/", response_model=List[ExperienceModel])
def list_experiences():
    return list(LOCAL_EXPERIENCE_VAULT.values())

@router.get("/{experience_id}", response_model=ExperienceModel)
def get_experience(experience_id: str):
    if experience_id not in LOCAL_EXPERIENCE_VAULT:
        raise HTTPException(status_code=404, detail=f"Experience '{experience_id}' not found")
    return LOCAL_EXPERIENCE_VAULT[experience_id]
