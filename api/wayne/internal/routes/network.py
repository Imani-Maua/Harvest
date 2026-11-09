from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dad.auth import User
from api.dad.session import session
from api.daisy.utils.auth_utils import get_current_user
from api.wayne.network.schema import NetworkCreate, NetworkOut, NetworkUpdate
from api.wayne.network.service import NetworkService

network_router = APIRouter(prefix="/network", tags=["Network"])


@network_router.post("", response_model=NetworkOut, status_code=status.HTTP_201_CREATED)
def create_network(
    body: NetworkCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return NetworkService.create(body=body, db=db)


@network_router.get("/{network_id}", response_model=NetworkOut)
def get_network(
    network_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return NetworkService.get(network_id=network_id, db=db)


@network_router.get("/by-job/{job_id}", response_model=NetworkOut)
def get_network_by_job(
    job_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return NetworkService.get_by_job(job_id=job_id, db=db)


@network_router.patch("/{network_id}", response_model=NetworkOut)
def update_network(
    network_id: int,
    body: NetworkUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return NetworkService.update(network_id=network_id, body=body, db=db)


@network_router.delete("/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_network(
    network_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    NetworkService.delete(network_id=network_id, db=db)
