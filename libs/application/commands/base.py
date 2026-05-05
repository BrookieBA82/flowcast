from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

from libs.application.context import AppContext


@dataclass
class CommandResult:
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None


class Command(ABC):
    @abstractmethod
    def execute(self, ctx: AppContext, args: Dict[str, Any]) -> CommandResult:
        pass