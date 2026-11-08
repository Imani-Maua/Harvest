from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.daisy.users.schema import LoginRequest, TokenOut, NewPassword
from api.daisy.tokens.service import TokenService
from api.daisy.utils.password_utils import verify_password, hash_password
from api.dad.auth import User


class UserService:

    @staticmethod
    def login(body: LoginRequest, db: Session) -> TokenOut:
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.pwd_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Elaine, is that you?",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        token = TokenService.create_and_store(user=user, db=db)
        return TokenOut(access_token=token, firstname=user.firstname)

    @staticmethod
    def set_new_password(user: User, body: NewPassword, db: Session):
        if not verify_password(body.current_password, user.pwd_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        user.pwd_hash = hash_password(body.new_password)
        db.commit()
        return {"message": "Password updated successfully"}
