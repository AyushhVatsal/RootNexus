from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    is_sufficient: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str

    missing_evidence: list[str] = Field(
        default_factory=list,
    )