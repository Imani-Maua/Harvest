from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

ContactRole = Literal["hiring_manager", "technical_recruiter", "peer"]


class ContactOut(BaseModel):
    name: Optional[str]
    email: str
    role: ContactRole


class NetworkCreate(BaseModel):
    job_applied_id: int
    hiring_manager: Optional[EmailStr] = None
    technical_recruiter: Optional[EmailStr] = None
    peers: Optional[list[EmailStr]] = None
    hiring_name: Optional[str] = None
    technical_name: Optional[str] = None
    peer_name: Optional[str] = None


class NetworkUpdate(BaseModel):
    hiring_manager: Optional[EmailStr] = None
    technical_recruiter: Optional[EmailStr] = None
    peers: Optional[list[EmailStr]] = None
    hiring_name: Optional[str] = None
    technical_name: Optional[str] = None
    peer_name: Optional[str] = None


class NetworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_applied_id: int
    hiring_manager: Optional[str]
    technical_recruiter: Optional[str]
    peers: Optional[list[str]]
    hiring_name: Optional[str]
    technical_name: Optional[str]
    peer_name: Optional[str]
