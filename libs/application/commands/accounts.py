from typing import Dict, Any

from libs.application.context import AppContext
from libs.application.commands.base import Command, CommandResult
from libs.domain.balance import Account


class AddAccountCommand(Command):
    def execute(self, ctx: AppContext, args: Dict[str, Any]) -> CommandResult:
        account_id = args["id"]

        if account_id in ctx.accounts:
            return CommandResult(False, f"Account {account_id} exists")

        ctx.accounts[account_id] = Account(
            id=account_id,
            name=args["name"],
            starting_balance=float(args["balance"]),
        )

        return CommandResult(True, f"Added account {account_id}")