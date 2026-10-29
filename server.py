# import sqlite3
# from contextlib import contextmanager
# from datetime import datetime, timezone
# from typing import Literal
# from pathlib import Path

# from mcp.server import MCPServer
# from mcp.server.mcpserver.exceptions import ToolError

# #DB_PA

# mcp = MCPServer(
#     "task-tracker-mcp",
#     instructions="Manage a simple to-do list: create, list and complete tasks."
# )

# tasks: dict[int, dict] = {}

# @mcp.tool()
# def create_task(title: str) -> dict:
#     """ Create a new task. Use this when the user wants to add something to their to-do list."""
#     title = title.strip()
#     if not title:
#         raise ToolError("Task title cannot be empty.")
    
#     task_id = max(tasks, default=0) + 1
#     task = {
#         "id": task_id,
#         "title": title,
#         "status": "open",
#         "created_at" : datetime.now(timezone.utc).isoformat()
#     }
    
#     tasks[task_id] = task
#     return task

# @mcp.tool()
# def list_tasks() -> list[dict]:
#     """ List all tasks. Use this when the user wants to see their to-do list."""
#     return list(tasks.values())

# @mcp.tool()
# def complete_task(task_id: int) -> dict:
#     """ Mark a task as completed. Use this when the user wants to mark a task as done."""
#     if task_id not in tasks:
#         raise ToolError(f"Task with ID {task_id} does not exist.")
    
#     tasks[task_id]["status"] = "completed"
#     return tasks[task_id]

import logging

from task_tracker import health  # noqa: F401  (importing registers /health and /ready)
from task_tracker.config import settings
from task_tracker.logging_config import configure_logging
from task_tracker.tools import mcp

configure_logging()
logger = logging.getLogger("task_tracker")

if __name__ == "__main__":
    if settings.server_transport == "streamable-http":
        logger.info(
            "Starting HTTP server on %s:%s", settings.server_host, settings.server_port
        )
        mcp.run(
            transport="streamable-http",
            host=settings.server_host,
            port=settings.server_port,
        )
    else:
        mcp.run(transport="stdio")
    
