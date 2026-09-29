import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AgentVault API",
    description="Multi-agent workflow risk intelligence powered by Hindsight experience memory",
    version="1.0.0"
)

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", ",".join(default_origins)).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = first_error.get("loc", [""])[-1]
    messages = {
        "service_name": "Service name is required.",
        "version": "Version is required.",
        "task_description": "Task description is required.",
        "workflow_type": "Workflow type is invalid or missing.",
        "environment": "Environment must be development, staging, or production.",
        "deployment_target": "Deployment target is invalid.",
    }
    message = messages.get(field, first_error.get("msg", "Invalid request information."))
    return JSONResponse(
        status_code=422,
        content={
            "error": "workflow_validation_error" if request.url.path == "/workflows/run" else "request_validation_error",
            "message": message,
            "details": [
                {
                    "loc": error.get("loc", ()),
                    "msg": error.get("msg", ""),
                    "type": error.get("type", ""),
                }
                for error in errors
            ],
        },
    )

@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception(
        "Unhandled API error for %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Unexpected server error.",
        },
    )

from app.api.workflows import router as workflows_router
from app.api.experiences import router as experiences_router
from app.api.risk_assessment import router as risk_router
from app.experience.seed import seed_hindsight_experiences

app.include_router(workflows_router)
app.include_router(experiences_router)
app.include_router(risk_router)

@app.post("/experiences/seed")
def seed_endpoint():
    count = seed_hindsight_experiences()
    return {"status": "seeded", "count": count}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "system": "AgentVault",
        "hindsight_configured": bool(os.getenv("HINDSIGHT_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
