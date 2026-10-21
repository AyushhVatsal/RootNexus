from pydantic import BaseModel, Field


class CorrelationResult(BaseModel):
    correlations: list[str] = Field(
        default_factory=list,
        description="Evidence relationships across sources",
    )