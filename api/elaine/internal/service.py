from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.dad.candidate import Candidate, CareerPreference, Project, Skill, SupportingLink, WorkExperience
from api.elaine.internal.schema import (
    CandidateCreate, CandidateUpdate,
    CareerPreferenceUpsert,
    ProjectCreate, ProjectUpdate,
    SkillCreate, SkillUpdate,
    SupportingLinkCreate, SupportingLinkUpdate,
    WorkExperienceCreate, WorkExperienceUpdate,
)

log = get_logger(__name__)


class CandidateService:

    @staticmethod
    def create(body: CandidateCreate, db: Session) -> Candidate:
        try:
            candidate = Candidate(**body.model_dump())
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
        except Exception as exc:
            db.rollback()
            log.error("candidate_create_failed", extra={"error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create candidate")
        log.info("candidate_created", extra={"candidate_id": candidate.id})
        return candidate

    @staticmethod
    def get(candidate_id: int, db: Session) -> Candidate:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            log.warning("candidate_not_found", extra={"candidate_id": candidate_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return candidate

    @staticmethod
    def update(candidate_id: int, body: CandidateUpdate, db: Session) -> Candidate:
        candidate = CandidateService.get(candidate_id, db)
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(candidate, field, value)
            db.commit()
            db.refresh(candidate)
        except Exception as exc:
            db.rollback()
            log.error("candidate_update_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update candidate")
        log.info("candidate_updated", extra={"candidate_id": candidate_id})
        return candidate

    @staticmethod
    def delete(candidate_id: int, db: Session) -> None:
        candidate = CandidateService.get(candidate_id, db)
        try:
            db.delete(candidate)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("candidate_delete_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete candidate")
        log.info("candidate_deleted", extra={"candidate_id": candidate_id})


class CareerPreferenceService:

    @staticmethod
    def get(candidate_id: int, db: Session) -> CareerPreference:
        CandidateService.get(candidate_id, db)
        pref = db.query(CareerPreference).filter(CareerPreference.candidate_id == candidate_id).first()
        if not pref:
            log.warning("career_preference_not_found", extra={"candidate_id": candidate_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career preference not found")
        return pref

    @staticmethod
    def upsert(candidate_id: int, body: CareerPreferenceUpsert, db: Session) -> CareerPreference:
        CandidateService.get(candidate_id, db)
        pref = db.query(CareerPreference).filter(CareerPreference.candidate_id == candidate_id).first()
        try:
            if pref:
                for field, value in body.model_dump(exclude_unset=True).items():
                    setattr(pref, field, value)
            else:
                pref = CareerPreference(candidate_id=candidate_id, **body.model_dump())
                db.add(pref)
            db.commit()
            db.refresh(pref)
        except Exception as exc:
            db.rollback()
            log.error("career_preference_upsert_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save career preference")
        log.info("career_preference_upserted", extra={"candidate_id": candidate_id})
        return pref

    @staticmethod
    def delete(candidate_id: int, db: Session) -> None:
        pref = CareerPreferenceService.get(candidate_id, db)
        try:
            db.delete(pref)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("career_preference_delete_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete career preference")
        log.info("career_preference_deleted", extra={"candidate_id": candidate_id})


class ProjectService:

    @staticmethod
    def create(candidate_id: int, body: ProjectCreate, db: Session) -> Project:
        CandidateService.get(candidate_id, db)
        try:
            project = Project(candidate_id=candidate_id, **body.model_dump())
            db.add(project)
            db.commit()
            db.refresh(project)
        except Exception as exc:
            db.rollback()
            log.error("project_create_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create project")
        log.info("project_created", extra={"candidate_id": candidate_id, "project_id": project.id})
        return project

    @staticmethod
    def list(candidate_id: int, db: Session) -> list[Project]:
        CandidateService.get(candidate_id, db)
        return db.query(Project).filter(Project.candidate_id == candidate_id).all()

    @staticmethod
    def get(candidate_id: int, project_id: int, db: Session) -> Project:
        CandidateService.get(candidate_id, db)
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.candidate_id == candidate_id,
        ).first()
        if not project:
            log.warning("project_not_found", extra={"candidate_id": candidate_id, "project_id": project_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    @staticmethod
    def update(candidate_id: int, project_id: int, body: ProjectUpdate, db: Session) -> Project:
        project = ProjectService.get(candidate_id, project_id, db)
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(project, field, value)
            db.commit()
            db.refresh(project)
        except Exception as exc:
            db.rollback()
            log.error("project_update_failed", extra={"project_id": project_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update project")
        log.info("project_updated", extra={"project_id": project_id})
        return project

    @staticmethod
    def delete(candidate_id: int, project_id: int, db: Session) -> None:
        project = ProjectService.get(candidate_id, project_id, db)
        try:
            db.delete(project)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("project_delete_failed", extra={"project_id": project_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete project")
        log.info("project_deleted", extra={"project_id": project_id})


class SkillService:

    @staticmethod
    def create(candidate_id: int, body: SkillCreate, db: Session) -> Skill:
        CandidateService.get(candidate_id, db)
        try:
            skill = Skill(candidate_id=candidate_id, **body.model_dump())
            db.add(skill)
            db.commit()
            db.refresh(skill)
        except Exception as exc:
            db.rollback()
            log.error("skill_create_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create skill")
        log.info("skill_created", extra={"candidate_id": candidate_id, "skill_id": skill.id})
        return skill

    @staticmethod
    def list(candidate_id: int, db: Session) -> list[Skill]:
        CandidateService.get(candidate_id, db)
        return db.query(Skill).filter(Skill.candidate_id == candidate_id).all()

    @staticmethod
    def get(candidate_id: int, skill_id: int, db: Session) -> Skill:
        CandidateService.get(candidate_id, db)
        skill = db.query(Skill).filter(
            Skill.id == skill_id,
            Skill.candidate_id == candidate_id,
        ).first()
        if not skill:
            log.warning("skill_not_found", extra={"candidate_id": candidate_id, "skill_id": skill_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
        return skill

    @staticmethod
    def update(candidate_id: int, skill_id: int, body: SkillUpdate, db: Session) -> Skill:
        skill = SkillService.get(candidate_id, skill_id, db)
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(skill, field, value)
            db.commit()
            db.refresh(skill)
        except Exception as exc:
            db.rollback()
            log.error("skill_update_failed", extra={"skill_id": skill_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update skill")
        log.info("skill_updated", extra={"skill_id": skill_id})
        return skill

    @staticmethod
    def delete(candidate_id: int, skill_id: int, db: Session) -> None:
        skill = SkillService.get(candidate_id, skill_id, db)
        try:
            db.delete(skill)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("skill_delete_failed", extra={"skill_id": skill_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete skill")
        log.info("skill_deleted", extra={"skill_id": skill_id})


class SupportingLinkService:

    @staticmethod
    def create(candidate_id: int, body: SupportingLinkCreate, db: Session) -> SupportingLink:
        CandidateService.get(candidate_id, db)
        try:
            link = SupportingLink(candidate_id=candidate_id, **body.model_dump())
            db.add(link)
            db.commit()
            db.refresh(link)
        except Exception as exc:
            db.rollback()
            log.error("link_create_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create link")
        log.info("link_created", extra={"candidate_id": candidate_id, "link_id": link.id})
        return link

    @staticmethod
    def list(candidate_id: int, db: Session) -> list[SupportingLink]:
        CandidateService.get(candidate_id, db)
        return db.query(SupportingLink).filter(SupportingLink.candidate_id == candidate_id).all()

    @staticmethod
    def get(candidate_id: int, link_id: int, db: Session) -> SupportingLink:
        CandidateService.get(candidate_id, db)
        link = db.query(SupportingLink).filter(
            SupportingLink.id == link_id,
            SupportingLink.candidate_id == candidate_id,
        ).first()
        if not link:
            log.warning("link_not_found", extra={"candidate_id": candidate_id, "link_id": link_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
        return link

    @staticmethod
    def update(candidate_id: int, link_id: int, body: SupportingLinkUpdate, db: Session) -> SupportingLink:
        link = SupportingLinkService.get(candidate_id, link_id, db)
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(link, field, value)
            db.commit()
            db.refresh(link)
        except Exception as exc:
            db.rollback()
            log.error("link_update_failed", extra={"link_id": link_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update link")
        log.info("link_updated", extra={"link_id": link_id})
        return link

    @staticmethod
    def delete(candidate_id: int, link_id: int, db: Session) -> None:
        link = SupportingLinkService.get(candidate_id, link_id, db)
        try:
            db.delete(link)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("link_delete_failed", extra={"link_id": link_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete link")
        log.info("link_deleted", extra={"link_id": link_id})


class WorkExperienceService:

    @staticmethod
    def create(candidate_id: int, body: WorkExperienceCreate, db: Session) -> WorkExperience:
        CandidateService.get(candidate_id, db)
        try:
            exp = WorkExperience(candidate_id=candidate_id, **body.model_dump())
            db.add(exp)
            db.commit()
            db.refresh(exp)
        except Exception as exc:
            db.rollback()
            log.error("work_experience_create_failed", extra={"candidate_id": candidate_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create work experience")
        log.info("work_experience_created", extra={"candidate_id": candidate_id, "experience_id": exp.id})
        return exp

    @staticmethod
    def list(candidate_id: int, db: Session) -> list[WorkExperience]:
        CandidateService.get(candidate_id, db)
        return db.query(WorkExperience).filter(WorkExperience.candidate_id == candidate_id).all()

    @staticmethod
    def get(candidate_id: int, experience_id: int, db: Session) -> WorkExperience:
        CandidateService.get(candidate_id, db)
        exp = db.query(WorkExperience).filter(
            WorkExperience.id == experience_id,
            WorkExperience.candidate_id == candidate_id,
        ).first()
        if not exp:
            log.warning("work_experience_not_found", extra={"candidate_id": candidate_id, "experience_id": experience_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience not found")
        return exp

    @staticmethod
    def update(candidate_id: int, experience_id: int, body: WorkExperienceUpdate, db: Session) -> WorkExperience:
        exp = WorkExperienceService.get(candidate_id, experience_id, db)
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(exp, field, value)
            db.commit()
            db.refresh(exp)
        except Exception as exc:
            db.rollback()
            log.error("work_experience_update_failed", extra={"experience_id": experience_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update work experience")
        log.info("work_experience_updated", extra={"experience_id": experience_id})
        return exp

    @staticmethod
    def delete(candidate_id: int, experience_id: int, db: Session) -> None:
        exp = WorkExperienceService.get(candidate_id, experience_id, db)
        try:
            db.delete(exp)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("work_experience_delete_failed", extra={"experience_id": experience_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete work experience")
        log.info("work_experience_deleted", extra={"experience_id": experience_id})
