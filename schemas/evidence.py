from pydantic import BaseModel, Field


class EvidenceAssessment(BaseModel):
    sufficient: bool
    reasoning: str

    coverage: float = Field(
        ge=0.0,
        le=1.0,
    )

    consistency: float = Field(
        ge=0.0,
        le=1.0,
    )

    temporal_correlation: float = Field(
        ge=0.0,
        le=1.0,
    )

    causal_support: float = Field(
        ge=0.0,
        le=1.0,
    )

    missing_evidence: list[str] = Field(
        default_factory=list,
    )