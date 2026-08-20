from pydantic import BaseModel, Field


class AgentFinding(BaseModel):
    agent: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)