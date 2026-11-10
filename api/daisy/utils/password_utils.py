import hashlib
import bcrypt


def hash_password(password: str) -> str:
    prehash = hashlib.sha256(password.encode()).hexdigest().encode()
    return bcrypt.hashpw(prehash, bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    prehash = hashlib.sha256(password.encode()).hexdigest().encode()
    return bcrypt.checkpw(prehash, hashed.encode())
