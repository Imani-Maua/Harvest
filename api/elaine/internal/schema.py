from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from api.dad.enums import EvidenceSource, WorkAuthorisation, RemotePreference, SkillCategory, SkillProficiency, LinkType, WorkArrangement, EmploymentType


class CandidateCreate(BaseModel):
    firstname: str
    lastname: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    work_authorisation: Optional[WorkAuthorisation] = None
    source: EvidenceSource = EvidenceSource.manual


class CandidateUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    work_authorisation: Optional[WorkAuthorisation] = None
    source: Optional[EvidenceSource] = None


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    firstname: str
    lastname: str
    email: str
    phone: Optional[str]
    location: Optional[str]
    headline: Optional[str]
    summary: Optional[str]
    work_authorisation: Optional[WorkAuthorisation]
    source: EvidenceSource
    created_at: datetime
    updated_at: datetime


class CareerPreferenceUpsert(BaseModel):
    desired_titles: Optional[List[str]] = None
    desired_industries: Optional[List[str]] = None
    desired_locations: Optional[List[str]] = None
    remote_preference: Optional[RemotePreference] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "GBP"
    open_to_contract: bool = False
    open_to_parttime: bool = False


class CareerPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    desired_titles: Optional[List[str]]
    desired_industries: Optional[List[str]]
    desired_locations: Optional[List[str]]
    remote_preference: Optional[RemotePreference]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: str
    open_to_contract: bool
    open_to_parttime: bool
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    repo_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    technologies: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    source: EvidenceSource = EvidenceSource.manual


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    repo_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    technologies: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    source: Optional[EvidenceSource] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    name: str
    description: Optional[str]
    url: Optional[str]
    repo_url: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    technologies: Optional[List[str]]
    highlights: Optional[List[str]]
    source: EvidenceSource


class SkillCreate(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.other
    proficiency: Optional[SkillProficiency] = None
    years_experience: Optional[int] = None
    source: EvidenceSource = EvidenceSource.manual


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[SkillCategory] = None
    proficiency: Optional[SkillProficiency] = None
    years_experience: Optional[int] = None
    source: Optional[EvidenceSource] = None


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    name: str
    category: SkillCategory
    proficiency: Optional[SkillProficiency]
    years_experience: Optional[int]
    source: EvidenceSource


class SupportingLinkCreate(BaseModel):
    link_type: LinkType
    label: Optional[str] = None
    url: str
    source: EvidenceSource = EvidenceSource.manual


class SupportingLinkUpdate(BaseModel):
    link_type: Optional[LinkType] = None
    label: Optional[str] = None
    url: Optional[str] = None
    source: Optional[EvidenceSource] = None


class SupportingLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    link_type: LinkType
    label: Optional[str]
    url: str
    source: EvidenceSource


class WorkExperienceCreate(BaseModel):
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    achievements: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    source: EvidenceSource = EvidenceSource.manual
    work_arrangement: Optional[WorkArrangement] = None
    employment_type: Optional[EmploymentType] = None


class WorkExperienceUpdate(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    source: Optional[EvidenceSource] = None
    work_arrangement: Optional[WorkArrangement] = None
    employment_type: Optional[EmploymentType] = None


class WorkExperienceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    company: str
    title: str
    location: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: bool
    description: Optional[str]
    achievements: Optional[List[str]]
    technologies: Optional[List[str]]
    source: EvidenceSource
    work_arrangement: Optional[WorkArrangement]
    employment_type: Optional[EmploymentType]


class CVUploadOut(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
