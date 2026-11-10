from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.warren.config import Settings

settings = Settings()

_url = (
    settings.DATABASE_URL
    .replace("postgresql+psycopg://", "postgresql+psycopg2://")
    .replace("postgres://", "postgresql+psycopg2://")
    .replace("postgresql://", "postgresql+psycopg2://")
)
engine = create_engine(_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
