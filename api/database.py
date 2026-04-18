"""
SQLAlchemy models for DeepSafe gateway.

Tables:
  users           — registered accounts (username + bcrypt hash)
  analysis_history — each prediction result, linked to user
"""

from __future__ import annotations

import os
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./deepsafe.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    history = relationship("AnalysisHistory", back_populates="user")


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    media_type = Column(String(16))
    ensemble_method = Column(String(16))
    verdict = Column(String(8))
    confidence = Column(Float)
    ensemble_score = Column(Float)
    model_results = Column(Text)  # JSON string
    timestamp = Column(String(32))

    user = relationship("User", back_populates="history")


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
