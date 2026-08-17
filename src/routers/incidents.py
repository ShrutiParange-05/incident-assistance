"""
/incidents endpoints — the core of the "Incident Analyzer" pipeline:

    POST /incidents  -> classify + get GenAI recommendation + persist
    GET  /incidents   -> list history (dashboard reads this)
    GET  /incidents/{id} -> single incident
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.database import get_db
from src.error_classifier import classify
from src.logging_config import log_extra
from src.models import Incident
from src.rag.assistant import generate_recommendation
from src.schemas import IncidentCreate, IncidentResponse

router = APIRouter(prefix="/incidents", tags=["incidents"])
logger = logging.getLogger("incident_assistant")


@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """
    Ingest a raw application error, run it through the classification +
    GenAI pipeline, persist the result, and return it.
    """
    logger.info(
        "Incoming incident",
        extra=log_extra(service=payload.service, error_code=payload.error_code),
    )

    try:
        classification = classify(payload.message, payload.error_code)
        recommendation, source_ids = generate_recommendation(
            service=payload.service,
            error_code=payload.error_code,
            message=payload.message,
            classification=classification,
        )

        incident = Incident(
            service=payload.service,
            error_code=payload.error_code,
            message=payload.message,
            error_type=classification.error_type,
            probable_cause=classification.probable_cause,
            severity=classification.severity,
            recommended_action=recommendation,
            rag_sources=",".join(source_ids),
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        logger.info(
            "Incident classified",
            extra=log_extra(
                incident_id=incident.id,
                error_type=classification.error_type,
                severity=classification.severity,
            ),
        )
        return incident

    except Exception:
        logger.exception(
            "Failed to process incident", extra=log_extra(service=payload.service)
        )
        raise HTTPException(status_code=500, detail="Failed to process incident")


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    limit: int = 50,
    service: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    """List recent incidents, optionally filtered by service/severity."""
    query = db.query(Incident)
    if service:
        query = query.filter(Incident.service == service)
    if severity:
        query = query.filter(Incident.severity == severity)
    return query.order_by(desc(Incident.created_at)).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
