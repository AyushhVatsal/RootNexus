from pydantic import BaseModel, Field


class Hypothesis(BaseModel):
    cause: str

    supporting_evidence: list[str] = Field(
        default_factory=list,
    )

    contradicting_evidence: list[str] = Field(
        default_factory=list,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )