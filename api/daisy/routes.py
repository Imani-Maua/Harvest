from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from api.warren.config import Settings
from api.daisy.users.schema import LoginRequest, TokenOut, UserOut, NewPassword
from api.daisy.users.service import UserService
from api.daisy.utils.auth_utils import get_current_user
from api.dad.session import session
from api.dad.auth import User

settings = Settings()
auth_router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


@auth_router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: Annotated[Session, Depends(session)],
    key: Optional[str] = Query(default=None),
):
    if not key or key != settings.LOGIN_SECRET:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return UserService.login(body=body, db=db)


@auth_router.post("/set_new_password")
def set_new_password(
    body: NewPassword,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
):
    return UserService.set_new_password(user=current_user, body=body, db=db)


@auth_router.get("/me", response_model=UserOut)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return UserOut.model_validate(current_user)
