from pydantic import BaseModel


class InvestigationTask(BaseModel):
    target: str
    reason: str
    priority: str

class InvestigationPlan(BaseModel):
    tasks: list[InvestigationTask]    