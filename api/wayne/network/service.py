from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.dad.job import Network
from api.wayne.network.schema import NetworkCreate, NetworkUpdate


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
