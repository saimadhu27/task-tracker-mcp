from task_tracker import repository
from task_tracker.db import session_scope
from task_tracker.errors import InvalidInput, TaskNotFound
from task_tracker.schemas import PRIORITIES, TaskOut
from datetime import date

MAX_TITLE_LENGTH = 500
VALID_FILTERS = {"all", "open", "done"}

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

def create_task(user_id: int, title: str, priority: str = "medium", due_date: date | None = None) -> TaskOut:
    title = _clean_title(title)
    _check_priority(priority)

    with session_scope() as session:
        task = repository.add_task(session, user_id, title, priority, due_date)
        return TaskOut.model_validate(task)
    
    with session_scope() as session:
        task = repository.add_task(session, user_id, title)
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
                due_date: date | None = None) -> TaskOut:
    with session_scope() as session:
        task = repository.get_task(session, user_id, task_id)
        if task is None:
            raise TaskNotFound(task_id)
        
        if title is not None:
            task.title = _clean_title(title)
        
        if priority is not None:
            _check_priority(priority)
            task.priority = priority
        
        if due_date is not None:
            task.due_date = due_date
        
        session.flush()
        return TaskOut.model_validate(task)

def complete_task(user_id: int, task_id:int) -> TaskOut:
    with session_scope() as session:
        task = repository.get_task(session, user_id, task_id)
        if task is None:
            raise TaskNotFound(task_id)
        task.status = "done"
        session.flush()
        return TaskOut.model_validate(task)
    