"""
Aggregation endpoint powering the simple dashboard (static/dashboard.html).
Keeps all "monitoring" math in one place instead of scattering counts
across the frontend.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Incident

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Incident.id)).scalar() or 0

    by_severity = dict(
        db.query(Incident.severity, func.count(Incident.id)).group_by(Incident.severity).all()
    )
    by_error_type = dict(
        db.query(Incident.error_type, func.count(Incident.id))
        .group_by(Incident.error_type)
        .all()
    )
    by_service = dict(
        db.query(Incident.service, func.count(Incident.id)).group_by(Incident.service).all()
    )

    recent = (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_incidents": total,
        "by_severity": by_severity,
        "by_error_type": by_error_type,
        "by_service": by_service,
        "recent": [i.to_dict() for i in recent],
    }
