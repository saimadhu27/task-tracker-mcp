from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from task_tracker.config import settings

from contextlib import contextmanager

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()