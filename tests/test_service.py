from datetime import timedelta

import pytest

from task_tracker import service
from task_tracker.errors import InvalidInput


def test_create_task_applies_defaults_and_trims_title(make_user):
    task = service.create_task(make_user(), "  Write report  ")

    assert task.title == "Write report"
    assert task.status == "open"
    assert task.priority == "medium"
    assert task.due_date is None


def test_create_task_rejects_empty_title(make_user):
    with pytest.raises(InvalidInput, match="cannot be empty"):
        service.create_task(make_user(), "   ")


def test_create_task_rejects_unknown_priority(make_user):
    with pytest.raises(InvalidInput, match="Priority must be one of"):
        service.create_task(make_user(), "Task", priority="urgent")


def test_create_task_rejects_past_due_date(make_user):
    yesterday = service.today() - timedelta(days=1)

    with pytest.raises(InvalidInput, match="in the past"):
        service.create_task(make_user(), "Task", due_date=yesterday)


def test_create_task_accepts_today_as_due_date(make_user):
    task = service.create_task(make_user(), "Task", due_date=service.today())

    assert task.due_date == service.today()


def test_list_tasks_filters_by_status(make_user):
    user_id = make_user()
    first = service.create_task(user_id, "First")
    service.create_task(user_id, "Second")
    service.complete_task(user_id, first.id)

    open_titles = [t.title for t in service.list_tasks(user_id, status="open")]
    done_titles = [t.title for t in service.list_tasks(user_id, status="done")]

    assert open_titles == ["Second"]
    assert done_titles == ["First"]


def test_list_tasks_orders_by_due_date_with_undated_last(make_user):
    user_id = make_user()
    today = service.today()
    service.create_task(user_id, "No date")
    service.create_task(user_id, "Later", due_date=today + timedelta(days=5))
    service.create_task(user_id, "Sooner", due_date=today + timedelta(days=1))

    titles = [t.title for t in service.list_tasks(user_id)]

    assert titles == ["Sooner", "Later", "No date"]


def test_update_task_can_clear_due_date(make_user):
    user_id = make_user()
    task = service.create_task(user_id, "Task", due_date=service.today())

    updated = service.update_task(user_id, task.id, clear_due_date=True)

    assert updated.due_date is None


def test_update_task_requires_at_least_one_field(make_user):
    user_id = make_user()
    task = service.create_task(user_id, "Task")

    with pytest.raises(InvalidInput, match="at least one field"):
        service.update_task(user_id, task.id)