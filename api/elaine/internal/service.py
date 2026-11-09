from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from api.dad.candidate import Candidate, CareerPreference, Project, Skill, SupportingLink, WorkExperience
from api.elaine.internal.schema import (
    CandidateCreate, CandidateUpdate,
    CareerPreferenceUpsert,
    ProjectCreate, ProjectUpdate,
    SkillCreate, SkillUpdate,
    SupportingLinkCreate, SupportingLinkUpdate,
    WorkExperienceCreate, WorkExperienceUpdate,
)


class CandidateService:

    @staticmethod
    def create(body: CandidateCreate, db: Session) -> Candidate:
        candidate = Candidate(**body.model_dump())
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    @staticmethod
    def get(candidate_id: int, db: Session) -> Candidate:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return candidate

    @staticmethod
    def update(candidate_id: int, body: CandidateUpdate, db: Session) -> Candidate:
        candidate = CandidateService.get(candidate_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(candidate, field, value)
        db.commit()
        db.refresh(candidate)
        return candidate

    @staticmethod
    def delete(candidate_id: int, db: Session) -> None:
        candidate = CandidateService.get(candidate_id, db)
        db.delete(candidate)
        db.commit()


class CareerPreferenceService:

    @staticmethod
    def get(candidate_id: int, db: Session) -> CareerPreference:
        CandidateService.get(candidate_id, db)
        pref = db.query(CareerPreference).filter(CareerPreference.candidate_id == candidate_id).first()
        if not pref:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career preference not found")
        return pref

    @staticmethod
    def upsert(candidate_id: int, body: CareerPreferenceUpsert, db: Session) -> CareerPreference:
        CandidateService.get(candidate_id, db)
        pref = db.query(CareerPreference).filter(CareerPreference.candidate_id == candidate_id).first()
        if pref:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(pref, field, value)
        else:
            pref = CareerPreference(candidate_id=candidate_id, **body.model_dump())
            db.add(pref)
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def delete(candidate_id: int, db: Session) -> None:
        pref = CareerPreferenceService.get(candidate_id, db)
        db.delete(pref)
        db.commit()


class ProjectService:

    @staticmethod
    def create(candidate_id: int, body: ProjectCreate, db: Session) -> Project:
        CandidateService.get(candidate_id, db)
        project = Project(candidate_id=candidate_id, **body.model_dump())
        db.add(project)
        db.commit()
        db.refresh(project)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    @staticmethod
    def update(candidate_id: int, project_id: int, body: ProjectUpdate, db: Session) -> Project:
        project = ProjectService.get(candidate_id, project_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(candidate_id: int, project_id: int, db: Session) -> None:
        project = ProjectService.get(candidate_id, project_id, db)
        db.delete(project)
        db.commit()


class SkillService:

    @staticmethod
    def create(candidate_id: int, body: SkillCreate, db: Session) -> Skill:
        CandidateService.get(candidate_id, db)
        skill = Skill(candidate_id=candidate_id, **body.model_dump())
        db.add(skill)
        db.commit()
        db.refresh(skill)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
        return skill

    @staticmethod
    def update(candidate_id: int, skill_id: int, body: SkillUpdate, db: Session) -> Skill:
        skill = SkillService.get(candidate_id, skill_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(skill, field, value)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def delete(candidate_id: int, skill_id: int, db: Session) -> None:
        skill = SkillService.get(candidate_id, skill_id, db)
        db.delete(skill)
        db.commit()


class SupportingLinkService:

    @staticmethod
    def create(candidate_id: int, body: SupportingLinkCreate, db: Session) -> SupportingLink:
        CandidateService.get(candidate_id, db)
        link = SupportingLink(candidate_id=candidate_id, **body.model_dump())
        db.add(link)
        db.commit()
        db.refresh(link)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
        return link

    @staticmethod
    def update(candidate_id: int, link_id: int, body: SupportingLinkUpdate, db: Session) -> SupportingLink:
        link = SupportingLinkService.get(candidate_id, link_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(link, field, value)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def delete(candidate_id: int, link_id: int, db: Session) -> None:
        link = SupportingLinkService.get(candidate_id, link_id, db)
        db.delete(link)
        db.commit()


class WorkExperienceService:

    @staticmethod
    def create(candidate_id: int, body: WorkExperienceCreate, db: Session) -> WorkExperience:
        CandidateService.get(candidate_id, db)
        exp = WorkExperience(candidate_id=candidate_id, **body.model_dump())
        db.add(exp)
        db.commit()
        db.refresh(exp)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience not found")
        return exp

    @staticmethod
    def update(candidate_id: int, experience_id: int, body: WorkExperienceUpdate, db: Session) -> WorkExperience:
        exp = WorkExperienceService.get(candidate_id, experience_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(exp, field, value)
        db.commit()
        db.refresh(exp)
        return exp

    @staticmethod
    def delete(candidate_id: int, experience_id: int, db: Session) -> None:
        exp = WorkExperienceService.get(candidate_id, experience_id, db)
        db.delete(exp)
        db.commit()
