from datetime import date
from typing import Any, Dict

from libs.application.commands.base import Command, CommandResult
from libs.domain.cashflow import CashFlowInstruction, CashFlowSeries


class AddSeriesCommand(Command):
    def execute(self, ctx, args: Dict[str, Any]) -> CommandResult:
        series_id = args["id"]

        if series_id in ctx.series:
            return CommandResult(False, f"Series {series_id} already exists")

        ctx.series[series_id] = CashFlowSeries(
            id=series_id,
            name=args["name"],
        )

        return CommandResult(True, f"Added series {series_id}")


class AddInstructionCommand(Command):
    def execute(self, ctx, args: Dict[str, Any]) -> CommandResult:
        instruction_id = args["id"]

        if instruction_id in ctx.instructions:
            return CommandResult(False, f"Instruction {instruction_id} already exists")

        series_id = args["series_id"]
        if series_id not in ctx.series:
            return CommandResult(False, f"Series {series_id} does not exist")

        ctx.instructions[instruction_id] = CashFlowInstruction(
            id=instruction_id,
            series_id=series_id,
            account_id=args["account_id"],
            amount=float(args["amount"]),
            recurrence=args["recurrence"],
            start_date=args["start_date"],
            end_date=args.get("end_date"),
        )

        return CommandResult(True, f"Added instruction {instruction_id}")


class EndInstructionCommand(Command):
    def execute(self, ctx, args: Dict[str, Any]) -> CommandResult:
        instruction_id = args["id"]
        end_date: date = args["end_date"]

        existing = ctx.instructions.get(instruction_id)
        if not existing:
            return CommandResult(False, f"Instruction {instruction_id} not found")

        if existing.end_date and existing.end_date <= end_date:
            return CommandResult(False, f"Instruction already ends on or before {existing.end_date}")

        ctx.instructions[instruction_id] = CashFlowInstruction(
            id=existing.id,
            series_id=existing.series_id,
            account_id=existing.account_id,
            amount=existing.amount,
            recurrence=existing.recurrence,
            start_date=existing.start_date,
            end_date=end_date,
        )

        return CommandResult(True, f"Instruction {instruction_id} now ends at {end_date}")


class ReplaceInstructionCommand(Command):
    def execute(self, ctx, args: Dict[str, Any]) -> CommandResult:
        instruction_id = args["id"]
        new_id = args["new_id"]
        effective_date: date = args["start_date"]

        existing = ctx.instructions.get(instruction_id)
        if not existing:
            return CommandResult(False, f"Instruction {instruction_id} not found")

        if new_id in ctx.instructions:
            return CommandResult(False, f"Instruction {new_id} already exists")

        ctx.instructions[instruction_id] = CashFlowInstruction(
            id=existing.id,
            series_id=existing.series_id,
            account_id=existing.account_id,
            amount=existing.amount,
            recurrence=existing.recurrence,
            start_date=existing.start_date,
            end_date=effective_date,
        )

        ctx.instructions[new_id] = CashFlowInstruction(
            id=new_id,
            series_id=existing.series_id,
            account_id=args.get("account_id", existing.account_id),
            amount=float(args.get("amount", existing.amount)),
            recurrence=args.get("recurrence", existing.recurrence),
            start_date=effective_date,
            end_date=args.get("end_date"),
        )

        return CommandResult(True, f"Replaced {instruction_id} with {new_id}")