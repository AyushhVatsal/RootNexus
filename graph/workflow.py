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


# ─────────────────────────────────────────────
# Routing after evidence assessment
# ─────────────────────────────────────────────

def route_after_evidence(state: IncidentState):

    assessment = state.get("evidence_assessment")

    if assessment is None:
        return "planner"

    if assessment.sufficient:
        return "hypothesis"

    return "planner"


# ─────────────────────────────────────────────
# Routing after validation
# ─────────────────────────────────────────────

def route_after_validation(state: IncidentState):

    validation = state.get("validation")

    if validation is None:
        return "planner"

    if validation.is_sufficient:
        return "final_report"

    return "planner"


# ─────────────────────────────────────────────
# Final report
# ─────────────────────────────────────────────

def final_report_node(state: IncidentState):

    hypothesis = None

    hypotheses = state.get(
        "hypotheses",
        [],
    )

    if hypotheses:
        hypothesis = hypotheses[-1]

    validation = state.get(
        "validation"
    )

    return {
        "final_report": (
            "Root cause investigation completed.\n\n"
            f"Root cause hypothesis:\n"
            f"{hypothesis.cause if hypothesis else 'N/A'}\n\n"
            f"Confidence:\n"
            f"{hypothesis.confidence if hypothesis else 'N/A'}\n\n"
            f"Validation:\n"
            f"{validation.reasoning if validation else 'N/A'}"
        ),
        "status": "completed",
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
        planner_node,
    )

    graph.add_node(
        "log_investigator",
        log_investigator_node,
    )

    graph.add_node(
        "metric_investigator",
        metric_investigator_node,
    )

    graph.add_node(
        "deployment_investigator",
        deployment_investigator_node,
    )

    graph.add_node(
        "database_investigator",
        database_investigator_node,
    )

    graph.add_node(
        "configuration_investigator",
        configuration_investigator_node,
    )

    graph.add_node(
        "correlator",
        correlator_node,
    )

    graph.add_node(
        "evidence_assessment",
        evidence_assessment_node,
    )

    graph.add_node(
        "hypothesis",
        hypothesis_node,
    )

    graph.add_node(
        "validator",
        validator_node,
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