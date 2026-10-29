import json
import logging

from task_tracker.db import database_is_ready
from task_tracker.logging_config import JsonFormatter


def test_database_is_ready_against_the_test_database():
    assert database_is_ready() is True


def test_json_formatter_includes_message_and_extra_fields():
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.tool = "create_task"

    data = json.loads(JsonFormatter().format(record))

    assert data["message"] == "hello world"
    assert data["level"] == "INFO"
    assert data["tool"] == "create_task"