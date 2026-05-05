from typing import Dict, Any

from libs.application.context import AppContext
from libs.application.commands.base import Command, CommandResult
from libs.domain.resolution import EventResolver


class ResolveCommand(Command):
    def execute(self, ctx: AppContext, args: Dict[str, Any]) -> CommandResult:
        resolver = EventResolver(
            settlement_log=ctx.settlement_log,
            start=args["start"],
            end=args["end"],
        )

        result = resolver.resolve(
            accounts=ctx.accounts,
            events=ctx.events,
            prior_states=args.get("states"),
        )

        return CommandResult(
            True,
            "Resolved",
            data={
                "states": result.account_states,
                "projections": result.balance_points,
            },
        )