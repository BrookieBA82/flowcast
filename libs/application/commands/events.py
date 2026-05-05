from typing import Dict, Any

from libs.application.context import AppContext
from libs.application.commands.base import Command, CommandResult


class GenerateEventsCommand(Command):
    def execute(self, ctx: AppContext, args: Dict[str, Any]) -> CommandResult:
        start = args["start"]
        end = args["end"]

        events = []

        for series in ctx.series.values():
            events.extend(
                series.events_for_series(
                    list(ctx.instructions.values()),
                    start,
                    end,
                )
            )

        ctx.events = events

        return CommandResult(True, f"Generated {len(events)} events")