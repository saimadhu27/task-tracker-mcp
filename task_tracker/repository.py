from sqlalchemy import select
from sqlalchemy.orm import Session

from task_tracker.models import Task, User

def get_user_by_email(session: Session, email:str) -> User | None:
    """Get a user by email."""
    return session.scalar(select(User).where(User.email == email))

def add_user(session: Session, email: str) -> User:
    """Add a new user."""
    user = User(email=email)
    session.add(user)
    session.flush()  # Ensure the user gets an ID
    return user

def add_task(session: Session, user_id: int, title: str) -> Task:
    task = Task(user_id=user_id, title=title)
    session.add(task)
    session.flush()
    session.refresh(task)  # Refresh to get the updated state from the database
    return task

def get_task(session: Session, user_id: int, task_id: int) -> Task | None:
    """Get a task by user ID and task ID."""
    return session.scalar(select(Task).where(Task.user_id == user_id, Task.id == task_id))

def list_tasks(session: Session, user_id: int, status: str | None) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id).order_by(Task.id)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    return list(session.scalars(stmt))
