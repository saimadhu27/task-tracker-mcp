import pytest
from sqlalchemy import text

from task_tracker import api_keys, repository
from task_tracker.auth import ApiKeyVerifier, get_current_user_id
from task_tracker.config import settings
from task_tracker.db import session_scope
from task_tracker.errors import AuthenticationRequired


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_generated_keys_are_unique_and_prefixed():
    first, second = api_keys.generate_key(), api_keys.generate_key()

    assert first != second
    assert first.startswith("tt_")


def test_key_is_stored_hashed_not_in_plain_text(make_user):
    _, key = api_keys.create_api_key(make_user(), "laptop")

    with session_scope() as session:
        stored = session.execute(text("SELECT key_hash FROM api_keys")).scalar_one()

    assert stored == api_keys.hash_key(key)
    assert stored != key


def test_each_key_resolves_to_its_own_user(make_user):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    _, alice_key = api_keys.create_api_key(alice, "laptop")
    _, bob_key = api_keys.create_api_key(bob, "laptop")

    assert api_keys.find_user_for_key(alice_key) == alice
    assert api_keys.find_user_for_key(bob_key) == bob


def test_unknown_key_is_rejected(make_user):
    api_keys.create_api_key(make_user(), "laptop")

    assert api_keys.find_user_for_key("tt_not-a-real-key") is None


def test_revoked_key_is_rejected(make_user):
    key_id, key = api_keys.create_api_key(make_user(), "laptop")

    with session_scope() as session:
        assert repository.revoke_api_key(session, key_id) is True

    assert api_keys.find_user_for_key(key) is None


@pytest.mark.anyio
async def test_verifier_accepts_a_valid_key(make_user):
    user_id = make_user()
    _, key = api_keys.create_api_key(user_id, "laptop")

    token = await ApiKeyVerifier().verify_token(key)

    assert token is not None
    assert token.client_id == str(user_id)
    assert "tasks" in token.scopes


@pytest.mark.anyio
async def test_verifier_rejects_an_unknown_key():
    assert await ApiKeyVerifier().verify_token("tt_nope") is None


def test_dev_user_fallback_when_auth_is_off():
    assert settings.auth_mode == "none"
    assert get_current_user_id() == get_current_user_id()


def test_missing_identity_is_refused_when_auth_is_on(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "api_key")

    with pytest.raises(AuthenticationRequired):
        get_current_user_id()