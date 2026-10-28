from contextlib import contextmanager
from typing import Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from task_tracker.errors import DomainError
from task_tracker.schemas import TaskOut
from task_tracker import service
from task_tracker.auth import get_current_user_id

mcp = MCPServer(
    "task-tracker",
    instructions="Manage a to-do list: create, list and complete tasks."
)

@contextmanager
def _translate_errors():
    """ Turn our own errors into messages the model can read and react to."""
    try:
        yield
    except DomainError as exc:
        raise ToolError(str(exc)) from exc
    
@mcp.tool()
def create_task(title: str) -> TaskOut:
    """ Create a new task. Use this when the user wants to add something to their to-do list."""
    with _translate_errors():
        return service.create_task(get_current_user_id(), title)
    
@mcp.tool()
def list_tasks(status: Literal["all", "open", "done"] = "all") -> list[TaskOut]:
    """ List the user's tasks. Optionally filter by status: 'open', 'done', or 'all' (the default)."""
    with _translate_errors():
        return service.list_tasks(get_current_user_id(), status)
    
@mcp.tool()
def complete_task(task_id: int) -> TaskOut:
    """Mark a task as done, given its numeric id. Use list_tasks first if you don't know the id."""
    with _translate_errors():
        return service.complete_task(get_current_user_id(), task_id)