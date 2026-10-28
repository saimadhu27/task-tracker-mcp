from contextlib import contextmanager
from typing import Literal
from datetime import date
import logging

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from task_tracker.errors import DomainError
from task_tracker.schemas import TaskOut, Priority
from task_tracker import service
from task_tracker.auth import get_current_user_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    except Exception as exc:
        logger.exception("Unexpected error in a tool call")
        raise ToolError("Something went wrong on the server. Please try again.") from exc

def _format_tasks(tasks: list[TaskOut]) -> str:
    if not tasks:
        return "No open tasks."
    lines = []
    for t in tasks:
        due = t.due_date.isoformat() if t.due_date else "no due date"
        lines.append(f"- [#{t.id}] {t.title} (priority: {t.priority}, due: {due})")
    return "\n".join(lines)

# ---- Tools: actions the model can take ----


@mcp.tool()
def create_task(
    title: str,
    priority: Priority = "medium",
    due_date: date | None = None,
) -> TaskOut:
    """Create a new task. Use this when the user wants to add something to their to-do list.

    priority is low, medium (default) or high. due_date is an ISO date like 2026-11-05
    and cannot be in the past.
    """
    with _translate_errors():
        return service.create_task(get_current_user_id(), title, priority, due_date)


@mcp.tool()
def list_tasks(
    status: Literal["all", "open", "done"] = "all",
    priority: Priority | None = None,
) -> list[TaskOut]:
    """List the user's tasks, soonest due date first. Both filters are optional and combine.

    Filter by status ('open', 'done' or 'all') and/or by priority.
    """
    with _translate_errors():
        return service.list_tasks(get_current_user_id(), status, priority)


@mcp.tool()
def update_task(
    task_id: int,
    title: str | None = None,
    priority: Priority | None = None,
    due_date: date | None = None,
    clear_due_date: bool = False,
) -> TaskOut:
    """Change an existing task, given its numeric id. Only the fields provided are changed.

    Set clear_due_date to true to remove the due date. Use list_tasks first if you
    don't know the id.
    """
    with _translate_errors():
        return service.update_task(
            get_current_user_id(), task_id, title, priority, due_date, clear_due_date
        )


@mcp.tool()
def complete_task(task_id: int) -> TaskOut:
    """Mark a task as done, given its numeric id. Use list_tasks first if you don't know the id."""
    with _translate_errors():
        return service.complete_task(get_current_user_id(), task_id)


# ---- Resource: read-only context an app can load ----


@mcp.resource("tasks://open", mime_type="text/markdown")
def open_tasks() -> str:
    """All of the user's open tasks, soonest due date first."""
    return _format_tasks(service.list_tasks(get_current_user_id(), status="open"))


# ---- Prompt: a template the user picks ----


@mcp.prompt()
def plan_my_week(focus: str = "") -> str:
    """Plan the week ahead from the user's open tasks."""
    tasks = service.list_tasks(get_current_user_id(), status="open")
    today = service.today()
    focus_line = f"\nThis week I especially want to focus on: {focus}\n" if focus else ""
    return (
        f"Today is {today:%A, %Y-%m-%d}. Here are my open tasks:\n\n"
        f"{_format_tasks(tasks)}\n{focus_line}\n"
        "Please plan my week. Put anything overdue or due soon first, spread the rest "
        "sensibly across the days, and point out any conflicts or tasks that look too big "
        "for one day."
    )