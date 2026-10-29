import json
import logging
import sys
from datetime import datetime, timezone

from task_tracker.config import settings

# Attributes every LogRecord has. Anything else came from logger.info(..., extra={...}).
_STANDARD_ATTRS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}

class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                entry[key] = value
        return json.dumps(entry, default=str)


def configure_logging() -> None:
    # Always stderr: in stdio mode, stdout belongs to the MCP protocol.
    handler = logging.StreamHandler(sys.stderr)
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(settings.log_level.upper())