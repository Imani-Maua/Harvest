from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.daisy.users.schema import LoginRequest, TokenOut, NewPassword
from api.daisy.tokens.service import TokenService
from api.daisy.utils.password_utils import verify_password, hash_password
from api.dad.auth import User

log = get_logger(__name__)


class UserService:

    @staticmethod
    def login(body: LoginRequest, db: Session) -> TokenOut:
        log.info("login_attempt", extra={"email": body.email})
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.pwd_hash):
            log.warning("login_failed_bad_credentials", extra={"email": body.email})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Elaine, is that you?",
            )
        if not user.is_active:
            log.warning("login_failed_inactive_account", extra={"user_id": user.id, "email": user.email})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        token = TokenService.create_and_store(user=user, db=db)
        log.info("login_success", extra={"user_id": user.id, "email": user.email})
        return TokenOut(access_token=token, firstname=user.firstname)

    @staticmethod
    def set_new_password(user: User, body: NewPassword, db: Session):
        if not verify_password(body.current_password, user.pwd_hash):
            log.warning("password_change_failed_wrong_current", extra={"user_id": user.id})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        try:
            user.pwd_hash = hash_password(body.new_password)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("password_change_db_error", extra={"user_id": user.id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password")
        log.info("password_change_success", extra={"user_id": user.id})
        return {"message": "Password updated successfully"}
