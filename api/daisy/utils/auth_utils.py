from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.dad.auth import User
from api.dad.session import session
from api.daisy.tokens.schema import Payload
from api.daisy.tokens.service import TokenService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

log = get_logger(__name__)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(session)],
) -> User:
    payload: Payload = TokenService.decode_token(token)
    user = db.query(User).filter(User.id == payload.id).first()
    if not user:
        log.warning("auth_user_not_found", extra={"user_id": payload.id})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not user.is_active:
        log.warning("auth_user_inactive", extra={"user_id": user.id})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user
