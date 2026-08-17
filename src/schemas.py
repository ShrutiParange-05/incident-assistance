"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    service: str = Field(..., examples=["payment-api"])
    error_code: int = Field(..., examples=[500])
    message: str = Field(..., examples=["Database connection timeout"])


class IncidentResponse(BaseModel):
    id: int
    service: str
    error_code: int
    message: str
    error_type: str
    probable_cause: str
    severity: str
    recommended_action: str
    rag_sources: list[str]
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    database: str
