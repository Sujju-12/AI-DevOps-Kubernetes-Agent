from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.schemas import InvestigationRecord


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    context: Mapped[str | None] = mapped_column(String(128), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(128), nullable=True)
    root_cause: Mapped[str] = mapped_column(Text)
    confidence: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))


_engine = None
SessionLocal = None


def init_db() -> None:
    global _engine, SessionLocal
    settings = get_settings()
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{path}", future=True)
    SessionLocal = sessionmaker(_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    with SessionLocal() as session:
        existing = session.scalar(select(User).where(User.username == settings.demo_username))
        if not existing:
            session.add(
                User(
                    username=settings.demo_username,
                    password_hash=hash_password(settings.demo_password),
                )
            )
            session.commit()


def authenticate(username: str, password: str) -> bool:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.username == username))
        if not user:
            return False
        return verify_password(password, user.password_hash)


def save_investigation(record: InvestigationRecord) -> None:
    with SessionLocal() as session:
        session.merge(
            Investigation(
                id=record.id,
                timestamp=datetime.fromisoformat(record.timestamp),
                context=record.context,
                namespace=record.namespace,
                root_cause=record.root_cause,
                confidence=record.confidence,
                status=record.status,
            )
        )
        session.commit()


def list_history(limit: int = 20) -> list[InvestigationRecord]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(Investigation).order_by(Investigation.timestamp.desc()).limit(limit)
        ).all()
        return [
            InvestigationRecord(
                id=row.id,
                timestamp=row.timestamp.astimezone(timezone.utc).isoformat(),
                context=row.context,
                namespace=row.namespace,
                root_cause=row.root_cause,
                confidence=row.confidence,
                status=row.status,
            )
            for row in rows
        ]
