from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from task_tracker.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

