import hashlib
import secrets

from task_tracker import repository
from task_tracker.db import session_scope

KEY_PREFIX = "tt_"

def generate_key() -> str:
    """256 bits of randomness, so it cannot be guessed."""
    return KEY_PREFIX + secrets.token_urlsafe(32)

def hash_key(key: str) -> str:
    # A fast hash is fine here: the key is 256 random bits, not a human-chosen
    # password. Passwords need slow hashes (bcrypt, argon2); random keys do not.
    return hashlib.sha256(key.encode()).hexdigest()

def create_api_key(user_id: int, name: str) -> tuple[int, str]:
    """Returns (key id, the key itself). The key is never stored and cannot be recovered."""
    key = generate_key()
    with session_scope() as session:
        row = repository.add_api_key(session, user_id, name, hash_key(key))
        return row.id, key

def find_user_for_key(key: str) -> int | None:
    with session_scope() as session:
        row = repository.get_active_api_key(session, hash_key(key))
        return row.user_id if row else None