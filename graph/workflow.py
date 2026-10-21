import logging

from langgraph.graph import END, START, StateGraph

from graph.state import IncidentState
from graph.router import investigation_router

from agents.planner import planner_node

from agents.log_investigator import log_investigator_node
from agents.metric_investigator import metric_investigator_node
from agents.deployment_investigator import deployment_investigator_node
from agents.database_investigator import database_investigator_node
from agents.configuration_investigator import configuration_investigator_node
from agents.evidence_assessment import evidence_assessment_node

from agents.correlator import correlator_node
from agents.hypothesis import hypothesis_node
from agents.validator import validator_node
from utils.llm_budget import with_invocation_budget

MAX_ITERATIONS = 3

logger = logging.getLogger("rootnexus.workflow")

def route_after_evidence(state: IncidentState):
    assessment = state.get("evidence_assessment")
    iteration = state.get("iteration", 0)

    if assessment is not None and assessment.sufficient:
        return "hypothesis"

    if iteration >= MAX_ITERATIONS:
        logger.info(
            "Evidence insufficient at iteration cap; "
            "proceeding with best-effort hypothesis."
        )
        return "hypothesis"

    return "planner"


def route_after_validation(state: IncidentState):
    validation = state.get("validation")
    iteration = state.get("iteration", 0)

    if validation is not None and validation.is_sufficient:
        return "final_report"

    if iteration >= MAX_ITERATIONS:
        logger.info(
            "Validation unsuccessful at iteration cap; "
            "producing inconclusive report."
        )
        return "final_report"

    return "planner"

# ─────────────────────────────────────────────
# Final report
# ─────────────────────────────────────────────

def _stop_reason(state: IncidentState) -> str:
    validation = state.get("validation")
    iteration = state.get("iteration", 0)

    if validation and validation.is_sufficient:
        return "Hypothesis validated with sufficient evidence."
    if not state.get("hypotheses"):
        return (
            f"Evidence was still insufficient after {iteration} "
            f"investigation round(s); no hypothesis was generated."
        )
    if iteration >= MAX_ITERATIONS:
        return (
            f"Reached the maximum of {MAX_ITERATIONS} investigation rounds "
            f"without a validated hypothesis."
        )
    return "The planner produced no actionable follow-up tasks."


def final_report_node(state: IncidentState):
    hypotheses = state.get("hypotheses", [])
    hypothesis = hypotheses[-1] if hypotheses else None
    validation = state.get("validation")

    completed = bool(validation and validation.is_sufficient)
    status = "completed" if completed else "inconclusive"
    heading = (
        "Root cause investigation completed."
        if completed
        else "Root cause investigation inconclusive."
    )
    reason = _stop_reason(state)

    # The validator's confidence is the calibrated one; the hypothesis agent's
    # own confidence is self-reported and shown only for reference.
    if validation:
        confidence = f"{validation.confidence:.2f} (validator)"
    elif hypothesis:
        confidence = f"{hypothesis.confidence:.2f} (hypothesis agent, unvalidated)"
    else:
        confidence = "N/A"

    missing = validation.missing_evidence if validation else []

    report = (
        f"{heading}\n"
        f"Reason: {reason}\n\n"
        f"Root cause hypothesis:\n"
        f"{hypothesis.cause if hypothesis else 'N/A'}\n\n"
        f"Confidence:\n{confidence}\n\n"
        f"Validation:\n{validation.reasoning if validation else 'N/A'}\n\n"
        f"Missing evidence:\n"
        f"{', '.join(missing) if missing else 'None'}\n\n"
        f"Investigation rounds: {state.get('iteration', 0)}"
    )

    return {
        "final_report": report,
        "stop_reason": reason,
        "status": status,
    }


# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_graph():

    graph = StateGraph(IncidentState)

    # ─────────────────────────────────────────
    # Nodes
    # ─────────────────────────────────────────

    graph.add_node(
        "planner",
        with_invocation_budget(planner_node),
    )

    graph.add_node(
        "log_investigator",
        with_invocation_budget(log_investigator_node),
    )

    graph.add_node(
        "metric_investigator",
        with_invocation_budget(metric_investigator_node),
    )

    graph.add_node(
        "deployment_investigator",
        with_invocation_budget(deployment_investigator_node),
    )

    graph.add_node(
        "database_investigator",
        with_invocation_budget(database_investigator_node),
    )

    graph.add_node(
        "configuration_investigator",
        with_invocation_budget(configuration_investigator_node),
    )

    graph.add_node(
        "correlator",
        with_invocation_budget(correlator_node),
    )

    graph.add_node(
        "evidence_assessment",
        with_invocation_budget(evidence_assessment_node),
    )

    graph.add_node(
        "hypothesis",
        with_invocation_budget(hypothesis_node),
    )

    graph.add_node(
        "validator",
        with_invocation_budget(validator_node),
    )

    graph.add_node(
        "final_report",
        final_report_node,
    )

    # ─────────────────────────────────────────
    # START
    # ─────────────────────────────────────────

    graph.add_edge(
        START,
        "planner",
    )

    # ─────────────────────────────────────────
    # PLANNER → DYNAMIC INVESTIGATORS
    # ─────────────────────────────────────────

    graph.add_conditional_edges(
        "planner",
        investigation_router,
    )

    # ─────────────────────────────────────────
    # INVESTIGATORS → CORRELATOR
    # ─────────────────────────────────────────

    graph.add_edge(
        "log_investigator",
        "correlator",
    )

    graph.add_edge(
        "metric_investigator",
        "correlator",
    )

    graph.add_edge(
        "deployment_investigator",
        "correlator",
    )

    graph.add_edge(
        "database_investigator",
        "correlator",
    )

    graph.add_edge(
        "configuration_investigator",
        "correlator",
    )

    # ─────────────────────────────────────────
    # CORRELATOR → HYPOTHESIS
    # ─────────────────────────────────────────

    graph.add_edge(
        "correlator",
        "evidence_assessment",
    )

    graph.add_conditional_edges(
        "evidence_assessment",
        route_after_evidence,
        {
            "hypothesis": "hypothesis",
            "planner": "planner",
        },
    )
    # ─────────────────────────────────────────
    # HYPOTHESIS → VALIDATOR
    # ─────────────────────────────────────────

    graph.add_edge(
        "hypothesis",
        "validator",
    )

    # ─────────────────────────────────────────
    # VALIDATOR → DYNAMIC ROUTING
    # ─────────────────────────────────────────

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "planner": "planner",
            "final_report": "final_report",
        },
    )

    # ─────────────────────────────────────────
    # FINAL
    # ─────────────────────────────────────────

    graph.add_edge(
        "final_report",
        END,
    )

    return graph.compile()