from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.dad.base import Base


class SponsorRegister(Base):
    __tablename__ = "sponsor_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # "GB" or "NL"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
