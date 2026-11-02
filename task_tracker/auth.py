from anyio import to_thread
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier

from task_tracker import api_keys, repository
from task_tracker.errors import AuthenticationRequired
from task_tracker.db import session_scope
from task_tracker.config import settings

SCOPE = "tasks"

def resource_url() -> str:
    return f"{settings.public_base_url.rstrip('/')}/mcp"

class ApiKeyVerifier(TokenVerifier):
    """Treats the bearer token as an API key and reports which user it belongs to."""
    async def verify_token(self, token: str) -> AccessToken | None:
        # The database lookup is blocking, so run it off the event loop.
        user_id = await to_thread.run_sync(api_keys.find_user_for_key, token)
        if user_id is None:
            return None # the SDK answers 401
        return AccessToken(
            token=token,
            client_id=str(user_id),
            scopes=[SCOPE],
            resource=resource_url(),
        )
        

def _dev_user_id() -> int:
    """Local development only: every request is the single dev user."""
    with session_scope() as session:
        user = repository.get_user_by_email(session, settings.dev_user_email)
        if user is None:
            user = repository.add_user(session, settings.dev_user_email)
        return user.id


def get_current_user_id() -> int:
    token = get_access_token()  # None on stdio and in the in-memory test client
    if token is not None:
        return int(token.client_id)
    if settings.auth_mode != "none":
        # The SDK already rejects unauthenticated HTTP requests. This is the backstop:
        # if identity is ever missing while auth is on, fail closed.
        raise AuthenticationRequired("Authentication is required.")
    return _dev_user_id() 
    