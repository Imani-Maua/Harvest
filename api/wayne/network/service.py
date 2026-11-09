from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.dad.job import JobApplied, Network
from api.wayne.network.schema import ContactOut, NetworkCreate, NetworkUpdate


class NetworkService:

    @staticmethod
    def create(body: NetworkCreate, db: Session) -> Network:
        existing = db.query(Network).filter(Network.job_applied_id == body.job_applied_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Network record already exists for this job",
            )
        network = Network(**body.model_dump())
        db.add(network)
        db.commit()
        db.refresh(network)
        return network

    @staticmethod
    def get(network_id: int, db: Session) -> Network:
        network = db.query(Network).filter(Network.id == network_id).first()
        if not network:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network record not found")
        return network

    @staticmethod
    def get_by_job(job_id: int, db: Session) -> Network:
        network = db.query(Network).filter(Network.job_applied_id == job_id).first()
        if not network:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network record not found")
        return network

    @staticmethod
    def update(network_id: int, body: NetworkUpdate, db: Session) -> Network:
        network = NetworkService.get(network_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(network, field, value)
        db.commit()
        db.refresh(network)
        return network

    @staticmethod
    def delete(network_id: int, db: Session) -> None:
        network = NetworkService.get(network_id, db)
        db.delete(network)
        db.commit()

    @staticmethod
    def get_by_company(company: str, db: Session) -> list[ContactOut]:
        networks = (
            db.query(Network)
            .join(JobApplied, Network.job_applied_id == JobApplied.id)
            .filter(JobApplied.company == company)
            .all()
        )
        contacts: list[ContactOut] = []
        for network in networks:
            if network.hiring_manager:
                contacts.append(ContactOut(name=network.hiring_name, email=network.hiring_manager, role="hiring_manager"))
            if network.technical_recruiter:
                contacts.append(ContactOut(name=network.technical_name, email=network.technical_recruiter, role="technical_recruiter"))
            if network.peers:
                for peer_email in network.peers:
                    contacts.append(ContactOut(name=network.peer_name, email=peer_email, role="peer"))
        return contacts
