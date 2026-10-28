class DomainError(Exception):
    """Base class for errors the business rules raise on purpose."""
    
class InvalidInput(DomainError):
    pass

class TaskNotFound(DomainError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"No task found with id {task_id}.")