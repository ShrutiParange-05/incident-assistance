"""
ORM models. One table: `incidents`, which stores every analyzed
error along with the classifier + GenAI assistant output so the
dashboard can query history.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # What came in
    service: Mapped[str] = mapped_column(String(120), index=True)
    error_code: Mapped[int] = mapped_column(Integer, index=True)
    message: Mapped[str] = mapped_column(Text)

    # What the classifier decided
    error_type: Mapped[str] = mapped_column(String(120), index=True)
    probable_cause: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), index=True)

    # What the GenAI assistant recommended
    recommended_action: Mapped[str] = mapped_column(Text)
    rag_sources: Mapped[str] = mapped_column(Text, default="")  # comma-separated doc ids used

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service": self.service,
            "error_code": self.error_code,
            "message": self.message,
            "error_type": self.error_type,
            "probable_cause": self.probable_cause,
            "severity": self.severity,
            "recommended_action": self.recommended_action,
            "rag_sources": self.rag_sources.split(",") if self.rag_sources else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
