from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.dad.job import JobApplied, Network
from api.wayne.network.schema import ContactOut, NetworkCreate, NetworkUpdate

log = get_logger(__name__)


class NetworkService:

    @staticmethod
    def create(body: NetworkCreate, db: Session) -> Network:
        existing = db.query(Network).filter(Network.job_applied_id == body.job_applied_id).first()
        if existing:
            log.warning("network_conflict", extra={"job_applied_id": body.job_applied_id})
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Network record already exists for this job",
            )
        try:
            network = Network(**body.model_dump())
            db.add(network)
            db.commit()
            db.refresh(network)
        except Exception as exc:
            db.rollback()
            log.error("network_create_failed", extra={"job_applied_id": body.job_applied_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create network record")
        log.info("network_created", extra={"network_id": network.id, "job_applied_id": network.job_applied_id})
        return network

    @staticmethod
    def get(network_id: int, db: Session) -> Network:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            log.warning("network_not_found", extra={"network_id": network_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network record not found")
        return network

    @staticmethod
    def get_by_job(job_id: int, db: Session) -> Network:
        network = db.query(Network).filter(Network.job_applied_id == job_id).first()
        if not network:
            log.warning("network_not_found_by_job", extra={"job_id": job_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network record not found")
        return network

    @staticmethod
    def update(network_id: int, body: NetworkUpdate, db: Session) -> Network:
        network = NetworkService.get(network_id, db)
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(network, field, value)
            db.commit()
            db.refresh(network)
        except Exception as exc:
            db.rollback()
            log.error("network_update_failed", extra={"network_id": network_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update network record")
        log.info("network_updated", extra={"network_id": network_id})
        return network

    @staticmethod
    def delete(network_id: int, db: Session) -> None:
        network = NetworkService.get(network_id, db)
        try:
            db.delete(network)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("network_delete_failed", extra={"network_id": network_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete network record")
        log.info("network_deleted", extra={"network_id": network_id})

    @staticmethod
    def get_by_company(company: str, db: Session) -> list[ContactOut]:
        try:
            networks = (
                db.query(Network)
                .join(JobApplied, Network.job_applied_id == JobApplied.id)
                .filter(JobApplied.company == company)
                .all()
            )
        except Exception as exc:
            log.error("network_by_company_failed", extra={"company": company, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve contacts")
        contacts: list[ContactOut] = []
        for network in networks:
            if network.hiring_manager:
                contacts.append(ContactOut(name=network.hiring_name, email=network.hiring_manager, role="hiring_manager"))
            if network.technical_recruiter:
                contacts.append(ContactOut(name=network.technical_name, email=network.technical_recruiter, role="technical_recruiter"))
            if network.peers:
                for peer_email in network.peers:
                    contacts.append(ContactOut(name=network.peer_name, email=peer_email, role="peer"))
        log.info("network_by_company", extra={"company": company, "contacts_returned": len(contacts)})
        return contacts
