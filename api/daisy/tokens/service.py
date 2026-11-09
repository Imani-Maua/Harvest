import hashlib
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import insert
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.warren.config import Settings
from api.dad.auth import AccessToken
from api.daisy.tokens.schema import Payload

settings = Settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 4

log = get_logger(__name__)


class TokenService:

    @staticmethod
    def create_and_store(user, db: Session) -> str:
        now = datetime.utcnow()
        expire = now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())

        payload_data = {
            "sub": user.email,
            "id": user.id,
            "jti": jti,
            "exp": expire,
            "iat": now,
        }
        token = jwt.encode(payload_data, SECRET_KEY, algorithm=ALGORITHM)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        try:
            db.execute(
                insert(AccessToken).values(
                    token_hash=token_hash,
                    user_id=user.id,
                    jti=jti,
                    expires_at=expire,
                    created_at=now,
                )
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("token_store_db_error", extra={"user_id": user.id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create session")
        log.info("token_created", extra={"user_id": user.id, "jti": jti})
        return token

    @staticmethod
    def decode_token(token: str) -> Payload:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return Payload(**payload)
        except ExpiredSignatureError:
            log.warning("token_expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            log.warning("token_invalid")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
