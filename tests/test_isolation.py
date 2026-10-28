import pytest

from task_tracker import service
from task_tracker.errors import TaskNotFound


def test_list_tasks_only_returns_own_tasks(make_user):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    service.create_task(alice, "Alice's task")
    service.create_task(bob, "Bob's task")

    assert [t.title for t in service.list_tasks(alice)] == ["Alice's task"]
    assert [t.title for t in service.list_tasks(bob)] == ["Bob's task"]


def test_cannot_complete_another_users_task(make_user):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    task = service.create_task(alice, "Alice's task")

    with pytest.raises(TaskNotFound):
        service.complete_task(bob, task.id)

    assert service.list_tasks(alice)[0].status == "open"


def test_cannot_update_another_users_task(make_user):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    task = service.create_task(alice, "Alice's task")

    with pytest.raises(TaskNotFound):
        service.update_task(bob, task.id, title="Hijacked")

    assert service.list_tasks(alice)[0].title == "Alice's task"