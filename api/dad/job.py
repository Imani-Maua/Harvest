from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.dad.enums import JobStatus, SponsorshipStatus
from api.dad.base import Base
from api.dad.outreach import OutreachContact


class JobApplied(Base):
    __tablename__ = "jobs_applied"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    job_status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.watch_list, nullable=False
    )
    job_url: Mapped[str | None] = mapped_column(String, nullable=True)
    applied_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sponsorship_status: Mapped[SponsorshipStatus | None] = mapped_column(
        Enum(SponsorshipStatus), nullable=True
    )
    sponsorship_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    network: Mapped["Network | None"] = relationship(
        "Network", back_populates="job_applied", uselist=False, cascade="all, delete-orphan"
    )
    outreach_contacts: Mapped[list[OutreachContact]] = relationship(
        "OutreachContact", back_populates="job_applied", cascade="all, delete-orphan"
    )


class Network(Base):
    __tablename__ = "network"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_applied_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs_applied.id"), nullable=False, unique=True
    )
    hiring_manager: Mapped[str | None] = mapped_column(String, nullable=True)
    technical_recruiter: Mapped[str | None] = mapped_column(String, nullable=True)
    peers: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    hiring_name: Mapped[str | None] = mapped_column(String, nullable=True)
    technical_name: Mapped[str | None] = mapped_column(String, nullable=True)
    peer_name: Mapped[str | None] = mapped_column(String, nullable=True)

    job_applied: Mapped["JobApplied"] = relationship("JobApplied", back_populates="network")
