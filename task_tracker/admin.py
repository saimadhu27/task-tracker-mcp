import argparse
import sys

from task_tracker import api_keys, repository
from task_tracker.db import session_scope


def create_user(email: str) -> None:
    with session_scope() as session:
        if repository.get_user_by_email(session, email) is not None:
            sys.exit(f"User {email} already exists.")
        user = repository.add_user(session, email)
        print(f"Created user {user.email} (id {user.id}).")


def create_key(email: str, name: str) -> None:
    name = name.strip()
    if not name or len(name) > 100:
        sys.exit("Key name must be between 1 and 100 characters.")
    with session_scope() as session:
        user = repository.get_user_by_email(session, email)
        if user is None:
            sys.exit(f"No user with email {email}. Run create-user first.")
        user_id = user.id
    key_id, key = api_keys.create_api_key(user_id, name)
    print(f"Created key #{key_id} '{name}' for {email}.")
    print("Copy it now. It is shown only once and cannot be recovered:")
    print(key)


def revoke_key(key_id: int) -> None:
    with session_scope() as session:
        if not repository.revoke_api_key(session, key_id):
            sys.exit(f"No active key with id {key_id}.")
    print(f"Revoked key #{key_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="task_tracker.admin")
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser("create-user", help="Create a user")
    p.add_argument("email")

    p = commands.add_parser("create-key", help="Create an API key for a user")
    p.add_argument("email")
    p.add_argument("--name", required=True, help="A label, such as 'laptop'")

    p = commands.add_parser("revoke-key", help="Revoke a key by its id")
    p.add_argument("key_id", type=int)

    args = parser.parse_args()
    if args.command == "create-user":
        create_user(args.email)
    elif args.command == "create-key":
        create_key(args.email, args.name)
    else:
        revoke_key(args.key_id)


if __name__ == "__main__":
    main()