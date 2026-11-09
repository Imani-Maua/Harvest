from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.dad.enums import HiringRole
from api.dad.base import Base

if TYPE_CHECKING:
    from api.dad.job import JobApplied


class OutreachContact(Base):
    __tablename__ = "outreach_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_applied_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs_applied.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str | None] = mapped_column(String, nullable=True)
    hiring_role: Mapped[HiringRole] = mapped_column(Enum(HiringRole), nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String, nullable=True)
    provenance: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    job_applied: Mapped[JobApplied] = relationship("JobApplied", back_populates="outreach_contacts")
