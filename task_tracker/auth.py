from task_tracker import repository
from task_tracker.db import session_scope
from task_tracker.config import settings

def get_current_user_id() -> int:
    """ Stand-in until real authentication arrives in Stage 7.
    Every request is treated as the single dev user from DEV_USER_EMAIL, created on first use."""
    with session_scope() as session:
        user = repository.get_user_by_email(session, settings.dev_user_email)
        if user is None:
            user = repository.add_user(session, settings.dev_user_email)
        return user.id