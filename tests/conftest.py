import os

# Point the app at the TEST database before anything from task_tracker is imported.
# Settings are read at import time, and environment variables beat the .env file.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://user:password@localhost:5432/tasks_test",
)
os.environ["DEV_USER_EMAIL"] = "dev@example.com"
os.environ["APP_TIMEZONE"] = "America/Los_Angeles"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402

from task_tracker import repository  # noqa: E402
from task_tracker.config import ROOT  # noqa: E402
from task_tracker.db import engine, session_scope  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    """Build the test schema from the real migrations, once per test run."""
    name = engine.url.database or ""
    assert name.endswith("_test"), f"Refusing to run tests against database {name!r}"

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(database):
    """Every test starts with empty tables and ids counting from 1."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE tasks, users RESTART IDENTITY CASCADE"))


@pytest.fixture
def make_user():
    def _make(email: str = "alice@example.com") -> int:
        with session_scope() as session:
            return repository.add_user(session, email).id

    return _make