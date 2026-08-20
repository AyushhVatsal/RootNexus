from typing import Any, Annotated, TypedDict

from schemas.incident import Incident
from schemas.finding import AgentFinding
from schemas.hypothesis import Hypothesis
from schemas.validation import ValidationResult
from schemas.evidence import EvidenceAssessment
from schemas.task import InvestigationTask

# ─────────────────────────────────────────────
# Reducers
# ─────────────────────────────────────────────

def append_findings(
    existing: list[AgentFinding],
    new: list[AgentFinding],
) -> list[AgentFinding]:
    return existing + new


def append_hypotheses(
    existing: list[Hypothesis],
    new: list[Hypothesis],
) -> list[Hypothesis]:
    return existing + new


def append_history(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return existing + new

def append_correlations(
    existing: list[str],
    new: list[str],
) -> list[str]:
    return existing + new


class IncidentState(TypedDict, total=False):

    # ─────────────────────────────
    # INCIDENT
    # ─────────────────────────────

    incident: Incident

    # ─────────────────────────────
    # RAW EVIDENCE
    # ─────────────────────────────

    logs: str
    metrics: dict[str, Any]
    deployments: list[dict[str, Any]]
    other_evidence: dict[str, Any]

    # ─────────────────────────────
    # PLANNING
    # ─────────────────────────────

    investigation_plan: list[InvestigationTask]

    current_task: InvestigationTask | None

    # ─────────────────────────────
    # INVESTIGATION FINDINGS
    # ─────────────────────────────

    agent_findings: Annotated[
        list[AgentFinding],
        append_findings,
    ]

    # ─────────────────────────────
    # CORRELATION
    # ─────────────────────────────

    correlations: Annotated[
        list[str],
        append_correlations,
    ]
    
    # Evidence sufficiency decision

    evidence_assessment: EvidenceAssessment

    # ─────────────────────────────
    # ROOT-CAUSE ANALYSIS
    # ─────────────────────────────

    hypotheses: Annotated[
        list[Hypothesis],
        append_hypotheses,
    ]

    validation: ValidationResult

    # ─────────────────────────────
    # MEMORY / HISTORY
    # ─────────────────────────────

    investigation_history: Annotated[
        list[dict[str, Any]],
        append_history,
    ]

    # ─────────────────────────────
    # WORKFLOW CONTROL
    # ─────────────────────────────

    iteration: int
    status: str
    next_action: str

    # ─────────────────────────────
    # OUTPUT
    # ─────────────────────────────

    final_report: str

    selected_tasks: list[InvestigationTask]
    
    completed_tasks: Annotated[
        list[str],
        lambda existing, new: existing + new,
    ]