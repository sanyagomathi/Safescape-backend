from sqlalchemy import String, Float, Integer, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)   # poor_lighting, harassment...
    gender: Mapped[str] = mapped_column(String(16), index=True)     # woman, man, unknown
    hour: Mapped[int] = mapped_column(Integer, index=True)          # 0..23
    rating: Mapped[float] = mapped_column(Float)                    # 0..1
    note: Mapped[str] = mapped_column(String(280), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_id: Mapped[str] = mapped_column(String(64), index=True)
    hour: Mapped[int] = mapped_column(Integer, index=True)

    overall: Mapped[float] = mapped_column(Float, default=0.5)      # 0..1
    women: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.3)   # 0..1
    anomaly: Mapped[bool] = mapped_column(Boolean, default=False)

    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SafePoint(Base):
    __tablename__ = "safe_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(24), index=True)   # police, medical, transit, commercial
    lat: Mapped[float] = mapped_column(Float, index=True)
    lng: Mapped[float] = mapped_column(Float, index=True)
    phone: Mapped[str] = mapped_column(String(32), default="")
    is_24x7: Mapped[bool] = mapped_column(Boolean, default=False)