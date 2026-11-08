from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.dad.auth import User
from api.dad.session import session
from api.daisy.tokens.schema import Payload
from api.daisy.tokens.service import TokenService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(session)],
) -> User:
    payload: Payload = TokenService.decode_token(token)
    user = db.query(User).filter(User.id == payload.id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user
