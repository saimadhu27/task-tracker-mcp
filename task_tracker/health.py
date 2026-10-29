from anyio import to_thread
from starlette.requests import Request
from starlette.responses import JSONResponse

from task_tracker.db import database_is_ready
from task_tracker.tools import mcp

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """ Liveness: the process is up. Never touches the database."""
    return JSONResponse({"status": "ok"})

@mcp.custom_route("/ready", methods=["GET"])
async def ready(request: Request) -> JSONResponse:
    """Readiness: the app can serve requests, which needs the database."""
    # The database check is blocking, so run it off the event loop.
    if await to_thread.run_sync(database_is_ready):
        return JSONResponse({"status": "ready"})
    return JSONResponse({"status": "database unavailable"}, status_code=503)