from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from task_tracker.config import settings

from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

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
        
def database_is_ready() -> bool:
    """True if the database answers a trivial query. Used by the /ready probe."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Database readiness check failed", exc_info=True)
        return False