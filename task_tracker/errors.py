class DomainError(Exception):
    """Base class for errors the business rules raise on purpose."""
    
class InvalidInput(DomainError):
    pass

class TaskNotFound(DomainError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"No task found with id {task_id}.")
        
class AuthenticationRequired(DomainError):
    pass

class RateLimited(DomainError):
    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Too many requests. Please wait {retry_after} seconds and try again.")
        self.retry_after = retry_after