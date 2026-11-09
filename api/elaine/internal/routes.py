from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.orm import Session
from api.dad.session import session
from api.dad.auth import User
from api.daisy.utils.auth_utils import get_current_user
from api.elaine.internal.schema import (
    CandidateCreate, CandidateUpdate, CandidateOut,
    CareerPreferenceUpsert, CareerPreferenceOut,
    ProjectCreate, ProjectUpdate, ProjectOut,
    SkillCreate, SkillUpdate, SkillOut,
    SupportingLinkCreate, SupportingLinkUpdate, SupportingLinkOut,
    WorkExperienceCreate, WorkExperienceUpdate, WorkExperienceOut,
    CVUploadOut,
)
from api.elaine.internal.service import (
    CandidateService,
    CareerPreferenceService,
    ProjectService,
    SkillService,
    SupportingLinkService,
    WorkExperienceService,
)
from api.elaine.internal.cv_parser.service import CVParserService

candidate_router = APIRouter(prefix="/candidates", tags=["Candidates"])


@candidate_router.post("", response_model=CandidateOut, status_code=status.HTTP_201_CREATED)
def create_candidate(
    body: CandidateCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return CandidateService.create(body=body, db=db)


@candidate_router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return CandidateService.get(candidate_id=candidate_id, db=db)


@candidate_router.patch("/{candidate_id}", response_model=CandidateOut)
def update_candidate(
    candidate_id: int,
    body: CandidateUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return CandidateService.update(candidate_id=candidate_id, body=body, db=db)


@candidate_router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    CandidateService.delete(candidate_id=candidate_id, db=db)


career_preference_router = APIRouter(
    prefix="/candidates/{candidate_id}/career-preference",
    tags=["Career Preference"],
)


@career_preference_router.get("", response_model=CareerPreferenceOut)
def get_career_preference(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return CareerPreferenceService.get(candidate_id=candidate_id, db=db)


@career_preference_router.put("", response_model=CareerPreferenceOut)
def upsert_career_preference(
    candidate_id: int,
    body: CareerPreferenceUpsert,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return CareerPreferenceService.upsert(candidate_id=candidate_id, body=body, db=db)


@career_preference_router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_career_preference(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    CareerPreferenceService.delete(candidate_id=candidate_id, db=db)


project_router = APIRouter(
    prefix="/candidates/{candidate_id}/projects",
    tags=["Projects"],
)


@project_router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    candidate_id: int,
    body: ProjectCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return ProjectService.create(candidate_id=candidate_id, body=body, db=db)


@project_router.get("", response_model=list[ProjectOut])
def list_projects(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return ProjectService.list(candidate_id=candidate_id, db=db)


@project_router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    candidate_id: int,
    project_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return ProjectService.get(candidate_id=candidate_id, project_id=project_id, db=db)


@project_router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    candidate_id: int,
    project_id: int,
    body: ProjectUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return ProjectService.update(candidate_id=candidate_id, project_id=project_id, body=body, db=db)


@project_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    candidate_id: int,
    project_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    ProjectService.delete(candidate_id=candidate_id, project_id=project_id, db=db)


skill_router = APIRouter(
    prefix="/candidates/{candidate_id}/skills",
    tags=["Skills"],
)


@skill_router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(
    candidate_id: int,
    body: SkillCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SkillService.create(candidate_id=candidate_id, body=body, db=db)


@skill_router.get("", response_model=list[SkillOut])
def list_skills(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SkillService.list(candidate_id=candidate_id, db=db)


@skill_router.get("/{skill_id}", response_model=SkillOut)
def get_skill(
    candidate_id: int,
    skill_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SkillService.get(candidate_id=candidate_id, skill_id=skill_id, db=db)


@skill_router.patch("/{skill_id}", response_model=SkillOut)
def update_skill(
    candidate_id: int,
    skill_id: int,
    body: SkillUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SkillService.update(candidate_id=candidate_id, skill_id=skill_id, body=body, db=db)


@skill_router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    candidate_id: int,
    skill_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    SkillService.delete(candidate_id=candidate_id, skill_id=skill_id, db=db)


supporting_link_router = APIRouter(
    prefix="/candidates/{candidate_id}/links",
    tags=["Supporting Links"],
)


@supporting_link_router.post("", response_model=SupportingLinkOut, status_code=status.HTTP_201_CREATED)
def create_link(
    candidate_id: int,
    body: SupportingLinkCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SupportingLinkService.create(candidate_id=candidate_id, body=body, db=db)


@supporting_link_router.get("", response_model=list[SupportingLinkOut])
def list_links(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SupportingLinkService.list(candidate_id=candidate_id, db=db)


@supporting_link_router.get("/{link_id}", response_model=SupportingLinkOut)
def get_link(
    candidate_id: int,
    link_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SupportingLinkService.get(candidate_id=candidate_id, link_id=link_id, db=db)


@supporting_link_router.patch("/{link_id}", response_model=SupportingLinkOut)
def update_link(
    candidate_id: int,
    link_id: int,
    body: SupportingLinkUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return SupportingLinkService.update(candidate_id=candidate_id, link_id=link_id, body=body, db=db)


@supporting_link_router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    candidate_id: int,
    link_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    SupportingLinkService.delete(candidate_id=candidate_id, link_id=link_id, db=db)


work_experience_router = APIRouter(
    prefix="/candidates/{candidate_id}/work-experiences",
    tags=["Work Experiences"],
)


@work_experience_router.post("", response_model=WorkExperienceOut, status_code=status.HTTP_201_CREATED)
def create_work_experience(
    candidate_id: int,
    body: WorkExperienceCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return WorkExperienceService.create(candidate_id=candidate_id, body=body, db=db)


@work_experience_router.get("", response_model=list[WorkExperienceOut])
def list_work_experiences(
    candidate_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return WorkExperienceService.list(candidate_id=candidate_id, db=db)


@work_experience_router.get("/{experience_id}", response_model=WorkExperienceOut)
def get_work_experience(
    candidate_id: int,
    experience_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return WorkExperienceService.get(candidate_id=candidate_id, experience_id=experience_id, db=db)


@work_experience_router.patch("/{experience_id}", response_model=WorkExperienceOut)
def update_work_experience(
    candidate_id: int,
    experience_id: int,
    body: WorkExperienceUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return WorkExperienceService.update(candidate_id=candidate_id, experience_id=experience_id, body=body, db=db)


@work_experience_router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_experience(
    candidate_id: int,
    experience_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    WorkExperienceService.delete(candidate_id=candidate_id, experience_id=experience_id, db=db)


cv_router = APIRouter(prefix="/cv", tags=["CV"])


@cv_router.post("/upload", response_model=CVUploadOut)
async def upload_cv(
    file: UploadFile,
    _: Annotated[User, Depends(get_current_user)],
):
    return await CVParserService.upload(file=file)


elaine_router = APIRouter()
elaine_router.include_router(candidate_router)
elaine_router.include_router(career_preference_router)
elaine_router.include_router(project_router)
elaine_router.include_router(skill_router)
elaine_router.include_router(supporting_link_router)
elaine_router.include_router(work_experience_router)
elaine_router.include_router(cv_router)
