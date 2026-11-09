from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.dad.enums import (
    EvidenceSource,
    WorkAuthorisation,
    RemotePreference,
    SkillCategory,
    SkillProficiency,
    LinkType,
)
from api.dad.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firstname: Mapped[str] = mapped_column(String, nullable=False)
    lastname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    headline: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_authorisation: Mapped[WorkAuthorisation | None] = mapped_column(
        Enum(WorkAuthorisation), nullable=True
    )
    source: Mapped[EvidenceSource] = mapped_column(
        Enum(EvidenceSource), default=EvidenceSource.manual, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    work_experiences: Mapped[list["WorkExperience"]] = relationship(
        "WorkExperience", back_populates="candidate", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="candidate", cascade="all, delete-orphan"
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill", back_populates="candidate", cascade="all, delete-orphan"
    )
    career_preference: Mapped["CareerPreference | None"] = relationship(
        "CareerPreference", back_populates="candidate",
        uselist=False, cascade="all, delete-orphan"
    )
    supporting_links: Mapped[list["SupportingLink"]] = relationship(
        "SupportingLink", back_populates="candidate", cascade="all, delete-orphan"
    )


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    achievements: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    technologies: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    source: Mapped[EvidenceSource] = mapped_column(
        Enum(EvidenceSource), default=EvidenceSource.manual, nullable=False
    )

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="work_experiences")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    repo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    technologies: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    highlights: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    source: Mapped[EvidenceSource] = mapped_column(
        Enum(EvidenceSource), default=EvidenceSource.manual, nullable=False
    )

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="projects")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[SkillCategory] = mapped_column(
        Enum(SkillCategory), default=SkillCategory.other, nullable=False
    )
    proficiency: Mapped[SkillProficiency | None] = mapped_column(
        Enum(SkillProficiency), nullable=True
    )
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[EvidenceSource] = mapped_column(
        Enum(EvidenceSource), default=EvidenceSource.manual, nullable=False
    )

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="skills")


class CareerPreference(Base):
    __tablename__ = "career_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), nullable=False)
    desired_titles: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    desired_industries: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    desired_locations: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    remote_preference: Mapped[RemotePreference | None] = mapped_column(
        Enum(RemotePreference), nullable=True
    )
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String, default="GBP", nullable=False)
    open_to_contract: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    open_to_parttime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="career_preference")


class SupportingLink(Base):
    __tablename__ = "supporting_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), nullable=False)
    link_type: Mapped[LinkType] = mapped_column(
        Enum(LinkType), default=LinkType.other, nullable=False
    )
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[EvidenceSource] = mapped_column(
        Enum(EvidenceSource), default=EvidenceSource.manual, nullable=False
    )

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="supporting_links")
