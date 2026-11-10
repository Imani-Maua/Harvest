from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    LOGIN_SECRET: str
    HUNTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    REED_API_KEY: str = ""
    JOOBLE_API_KEY: str = ""
    GITHUB_PAT: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"
