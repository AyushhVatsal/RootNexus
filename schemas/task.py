from typing import Literal
from pydantic import BaseModel

InvestigationTarget = Literal[
    "logs",
    "metrics",
    "deployment",
    "database",
    "configuration",
]

class InvestigationTask(BaseModel):
    target: InvestigationTarget
    reason: str
    priority: str

class InvestigationPlan(BaseModel):
    tasks: list[InvestigationTask]    