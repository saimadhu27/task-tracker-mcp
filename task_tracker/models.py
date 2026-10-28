from datetime import datetime, date

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'done')", name="ck_tasks_status"),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_tasks_priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10), server_default="open")
    priority: Mapped[str] = mapped_column(String(10), server_default="medium")
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )