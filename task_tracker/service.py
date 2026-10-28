from task_tracker import repository
from task_tracker.db import session_scope
from task_tracker.errors import InvalidInput, TaskNotFound
from task_tracker.schemas import PRIORITIES, TaskOut
from task_tracker.config import settings

from datetime import date, datetime
from zoneinfo import ZoneInfo

MAX_TITLE_LENGTH = 500
VALID_FILTERS = {"all", "open", "done"}

def today() -> date:
    """ Todayy's date in the user's time zone, not the server's."""
    return datetime.now(ZoneInfo(settings.app_timezone)).date()

def _clean_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise InvalidInput("The task title cannot be empty.")
    if len(title) > MAX_TITLE_LENGTH:
        raise InvalidInput(f"The task title cannot exceed {MAX_TITLE_LENGTH} characters.")
    return title

def _check_priority(priority: str) -> None:
    if priority not in PRIORITIES:
        raise InvalidInput(f"Priority must be one of {', '.join(PRIORITIES)}.")
    
def _check_due_date(due_date: date | None) -> None:
    if due_date is not None and due_date < today():
        raise InvalidInput(
            f"The due date {due_date.isoformat()} is in the past (today is {today().isoformat()})."
        )

def create_task(user_id: int, title: str, priority: str = "medium", due_date: date | None = None) -> TaskOut:
    title = _clean_title(title)
    _check_priority(priority)
    _check_due_date(due_date)
    with session_scope() as session:
        task = repository.add_task(session, user_id, title, priority, due_date)
        return TaskOut.model_validate(task)
    
def list_tasks(user_id: int, status: str = "all", priority: str | None = None) -> list[TaskOut]:
    if status not in VALID_FILTERS:
        raise InvalidInput(f"Invalid status filter: {status}. Valid filters are: {', '.join(VALID_FILTERS)}")
    if priority is not None:
        _check_priority(priority)
    
    with session_scope() as session:
        rows = repository.list_tasks(session, user_id, status=None if status == "all" else status, priority=priority)
        return [TaskOut.model_validate(r) for r in rows]
    
def update_task(user_id: int, 
                task_id:int, 
                title: str | None = None, 
                priority: str | None = None,
                due_date: date | None = None,
                clear_due_date: bool = False,) -> TaskOut:
    if title is None and priority is None and due_date is None and not clear_due_date:
        raise InvalidInput("Provide at least one field to change.")
    if due_date is not None and clear_due_date:
        raise InvalidInput("Provide either due_date or clear_due_date, not both.")
    if title is not None:
        title = _clean_title(title)
    if priority is not None:
        _check_priority(priority)
    _check_due_date(due_date)

    with session_scope() as session:
        task = repository.get_task(session, user_id, task_id)
        if task is None:
            raise TaskNotFound(task_id)

        if title is not None:
            task.title = title
        if priority is not None:
            task.priority = priority
        if due_date is not None:
            task.due_date = due_date
        if clear_due_date:
            task.due_date = None

        session.flush()
        return TaskOut.model_validate(task)


def complete_task(user_id: int, task_id: int) -> TaskOut:
    with session_scope() as session:
        task = repository.get_task(session, user_id, task_id)
        if task is None:
            raise TaskNotFound(task_id)
        task.status = "done"
        session.flush()
        return TaskOut.model_validate(task)