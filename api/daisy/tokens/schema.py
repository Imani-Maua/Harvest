from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Payload(BaseModel):
    sub: str
    id: int
    jti: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
