from task_tracker import repository
from task_tracker.db import session_scope
from task_tracker.errors import InvalidInput, TaskNotFound
from task_tracker.schemas import TaskOut

MAX_TITLE_LENGTH = 500
VALID_FILTERS = {"all", "open", "done"}

def create_task(user_id: int, title: str) -> TaskOut:
    title = title.strip()
    if not title:
        raise InvalidInput(" The task title cannot be empty.")
    if len(title) > MAX_TITLE_LENGTH:
        raise InvalidInput(f"The task title cannot exceed {MAX_TITLE_LENGTH} characters.")
    
    with session_scope() as session:
        task = repository.add_task(session, user_id, title)
        return TaskOut.model_validate(task)
    
def list_tasks(user_id: int, status: str = "all") -> list[TaskOut]:
    if status not in VALID_FILTERS:
        raise InvalidInput(f"Invalid status filter: {status}. Valid filters are: {', '.join(VALID_FILTERS)}")
    
    with session_scope() as session:
        rows = repository.list_tasks(session, user_id, None if status == "all" else status)
        return [TaskOut.model_validate(r) for r in rows]
    
def complete_task(user_id: int, task_id:int) -> TaskOut:
    with session_scope() as session:
        task = repository.get_task(session, user_id, task_id)
        if task is None:
            raise TaskNotFound(task_id)
        task.status = "done"
        session.flush()
        return TaskOut.model_validate(task)
    