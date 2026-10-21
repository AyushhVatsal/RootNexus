from types import SimpleNamespace

from graph.router import investigation_router
from graph.workflow import (
    MAX_ITERATIONS,
    route_after_evidence,
    route_after_validation,
)


def test_failed_validation_routes_to_planner_before_cap():
    state = {
        "iteration": 1,
        "validation": SimpleNamespace(is_sufficient=False),
    }
    assert route_after_validation(state) == "planner"


def test_failed_validation_routes_to_report_at_cap():
    state = {
        "iteration": MAX_ITERATIONS,
        "validation": SimpleNamespace(is_sufficient=False),
    }
    assert route_after_validation(state) == "final_report"


def test_sufficient_validation_routes_to_report():
    state = {
        "iteration": 1,
        "validation": SimpleNamespace(is_sufficient=True),
    }
    assert route_after_validation(state) == "final_report"


def test_insufficient_evidence_retries_before_cap():
    state = {
        "iteration": 1,
        "evidence_assessment": SimpleNamespace(sufficient=False),
    }
    assert route_after_evidence(state) == "planner"


def test_insufficient_evidence_routes_to_hypothesis_at_cap():
    state = {
        "iteration": MAX_ITERATIONS,
        "evidence_assessment": SimpleNamespace(sufficient=False),
    }
    assert route_after_evidence(state) == "hypothesis"


def test_sufficient_evidence_routes_to_hypothesis():
    state = {
        "iteration": 1,
        "evidence_assessment": SimpleNamespace(sufficient=True),
    }
    assert route_after_evidence(state) == "hypothesis"


def test_empty_plan_routes_to_final_report():
    assert investigation_router({"investigation_plan": []}) == "final_report"


def test_unknown_targets_route_to_final_report():
    task = SimpleNamespace(target="unknown-source")
    assert investigation_router({"investigation_plan": [task]}) == "final_report"
