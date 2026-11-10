from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.warren.config import Settings

settings = Settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
