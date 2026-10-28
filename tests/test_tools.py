import pytest
from mcp import Client

from task_tracker.tools import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as c:
        yield c


@pytest.mark.anyio
async def test_expected_tools_are_listed(client):
    result = await client.list_tools()

    names = {tool.name for tool in result.tools}

    assert names == {"create_task", "list_tasks", "update_task", "complete_task"}


@pytest.mark.anyio
async def test_create_then_list_round_trip(client):
    created = await client.call_tool("create_task", {"title": "Write tests", "priority": "high"})
    assert not created.is_error
    assert created.structured_content["title"] == "Write tests"
    assert created.structured_content["priority"] == "high"

    listed = await client.call_tool("list_tasks", {})
    assert not listed.is_error
    titles = [t["title"] for t in listed.structured_content["result"]]
    assert titles == ["Write tests"]


@pytest.mark.anyio
async def test_rule_violation_comes_back_as_a_readable_error(client):
    result = await client.call_tool("create_task", {"title": "   "})

    assert result.is_error
    assert "cannot be empty" in result.content[0].text


@pytest.mark.anyio
async def test_open_tasks_resource_lists_open_tasks(client):
    await client.call_tool("create_task", {"title": "Resource check"})

    result = await client.read_resource("tasks://open")

    assert "Resource check" in result.contents[0].text