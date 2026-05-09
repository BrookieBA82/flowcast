import sys
from datetime import date

from libs.application.commands.accounts import AddAccountCommand
from libs.application.commands.instructions import AddInstructionCommand
from libs.application.commands.events import GenerateEventsCommand
from libs.application.commands.resolution import ResolveCommand

from libs.persistence.repository import JsonRepository


def _parse_args(parts: list[str]) -> dict:
    parsed = {}

    for p in parts:
        if "=" not in p:
            raise ValueError(f"Invalid argument: {p}")

        key, value = p.split("=", 1)

        parsed[key] = _coerce(value)

    return parsed


def _coerce(value: str):
    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    try:
        return date.fromisoformat(value)
    except ValueError:
        pass

    return value


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m clients.cli.main <repo.json>")
        return

    repo_path = sys.argv[1]

    repo = JsonRepository(repo_path)

    ctx = repo.load()

    commands = {
        "add-account": AddAccountCommand(),
        "add-instruction": AddInstructionCommand(),
        "generate-events": GenerateEventsCommand(),
        "resolve": ResolveCommand(),
    }

    try:
        while True:
            raw = input(">> ").strip()

            if not raw:
                continue

            if raw in ("exit", "quit"):
                break

            parts = raw.split()

            cmd_name = parts[0]
            arg_parts = parts[1:]

            if cmd_name not in commands:
                print(f"Unknown command: {cmd_name}")
                continue

            try:
                args = _parse_args(arg_parts)

                result = commands[cmd_name].execute(ctx, args)

                print(result.message)

            except Exception as e:
                print(f"ERROR: {e}")

    finally:
        repo.save(ctx)
        print(f"Saved repository to {repo_path}")


if __name__ == "__main__":
    main()