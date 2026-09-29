from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.experience import ExperienceModel
from app.experience.retain import (
    LOCAL_EXPERIENCE_VAULT,
    get_stored_experience,
    list_stored_experiences,
    retain_experience,
)

router = APIRouter(prefix="/experiences", tags=["experiences"])

@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_experience(exp: ExperienceModel):
    result = retain_experience(exp)
    return result

@router.get("", response_model=List[ExperienceModel])
@router.get("/", response_model=List[ExperienceModel])
def list_experiences():
    return list_stored_experiences()

@router.get("/{experience_id}", response_model=ExperienceModel)
def get_experience(experience_id: str):
    experience = get_stored_experience(experience_id)
    if experience is None:
        raise HTTPException(status_code=404, detail=f"Experience '{experience_id}' not found")
    LOCAL_EXPERIENCE_VAULT[experience_id] = experience
    return experience
