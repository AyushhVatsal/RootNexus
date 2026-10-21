
"""Graph-loop integration tests using fake nodes.

Verifies that failed validation triggers another investigation round,
follow-up tasks reach the correct investigator, and the iteration cap
terminates the graph without real LLM or network calls.
"""

from datetime import datetime

import graph.workflow as wf
from schemas.evidence import EvidenceAssessment
from schemas.finding import AgentFinding
from schemas.hypothesis import Hypothesis
from schemas.incident import Incident
from schemas.task import InvestigationTask
from schemas.validation import ValidationResult
from utils.llm_budget import LLMBudget


def test_failed_validation_triggers_second_investigation_round(monkeypatch):
    calls = {"planner": 0, "validator": 0, "config": 0}

    def planner(state):
        calls["planner"] += 1
        target = "logs" if calls["planner"] == 1 else "configuration"

        return {
            "investigation_plan": [
                InvestigationTask(
                    target=target,
                    reason="Test investigation task",
                    priority="high",
                )
            ],
            "iteration": state.get("iteration", 0) + 1,
        }

    def logs(state):
        return {
            "agent_findings": [
                AgentFinding(
                    agent="log_investigator",
                    summary="Test log finding",
                    evidence=["Test log evidence"],
                    confidence=0.5,
                )
            ],
            "completed_tasks": ["logs"],
        }

    def config(state):
        calls["config"] += 1
        return {
            "agent_findings": [
                AgentFinding(
                    agent="configuration_investigator",
                    summary="Test configuration finding",
                    evidence=["Test configuration evidence"],
                    confidence=0.7,
                )
            ],
            "completed_tasks": ["configuration"],
        }

    def correlator(state):
        return {
            "correlations": ["Test correlation"],
            "investigation_history": [
                {"iteration": state.get("iteration", 0)}
            ],
        }

    def assessment(state):
        return {
            "evidence_assessment": EvidenceAssessment(
                sufficient=True,
                reasoning="Test evidence is sufficient.",
                coverage=1.0,
                consistency=1.0,
                temporal_correlation=1.0,
                causal_support=1.0,
            )
        }

    def hypothesis(state):
        return {
            "hypotheses": [
                Hypothesis(
                    cause="Database connection pool exhaustion",
                    supporting_evidence=["Test evidence"],
                    confidence=0.8,
                )
            ]
        }

    def validator(state):
        calls["validator"] += 1
        sufficient = calls["validator"] >= 2

        return {
            "validation": ValidationResult(
                is_sufficient=sufficient,
                confidence=0.9 if sufficient else 0.4,
                reasoning=(
                    "Test validation passed."
                    if sufficient
                    else "More configuration evidence is needed."
                ),
                missing_evidence=(
                    []
                    if sufficient
                    else ["Configuration before the incident"]
                ),
            )
        }

    monkeypatch.setattr(wf, "planner_node", planner)
    monkeypatch.setattr(wf, "log_investigator_node", logs)
    monkeypatch.setattr(wf, "metric_investigator_node", logs)
    monkeypatch.setattr(wf, "deployment_investigator_node", logs)
    monkeypatch.setattr(wf, "database_investigator_node", logs)
    monkeypatch.setattr(wf, "configuration_investigator_node", config)
    monkeypatch.setattr(wf, "correlator_node", correlator)
    monkeypatch.setattr(wf, "evidence_assessment_node", assessment)
    monkeypatch.setattr(wf, "hypothesis_node", hypothesis)
    monkeypatch.setattr(wf, "validator_node", validator)

    budget = LLMBudget()

    result = wf.build_graph().invoke(
        {
            "incident": Incident(
                incident_id="INC-1",
                service="payment-api",
                description="Test incident",
                started_at=datetime(2026, 8, 20, 10),
            ),
            "iteration": 0,
        },
        config={"configurable": {"llm_budget": budget}},
    )

    assert calls["planner"] == 2
    assert calls["validator"] == 2
    assert calls["config"] == 1
    assert result["iteration"] == 2
    assert result["status"] == "completed"
    assert "0.90 (validator)" in result["final_report"]


def test_loop_stops_at_iteration_cap(monkeypatch):
    calls = {"planner": 0, "validator": 0}

    def planner(state):
        calls["planner"] += 1
        return {
            "investigation_plan": [
                InvestigationTask(
                    target="logs",
                    reason="Test repeated investigation",
                    priority="high",
                )
            ],
            "iteration": state.get("iteration", 0) + 1,
        }

    def logs(state):
        return {"completed_tasks": ["logs"]}

    def correlator(state):
        return {"correlations": ["Test correlation"]}

    def assessment(state):
        return {
            "evidence_assessment": EvidenceAssessment(
                sufficient=True,
                reasoning="Test evidence is sufficient.",
                coverage=1.0,
                consistency=1.0,
                temporal_correlation=1.0,
                causal_support=1.0,
            )
        }

    def hypothesis(state):
        return {
            "hypotheses": [
                Hypothesis(
                    cause="Test root cause",
                    supporting_evidence=["Test evidence"],
                    confidence=0.5,
                )
            ]
        }

    def validator(state):
        calls["validator"] += 1
        return {
            "validation": ValidationResult(
                is_sufficient=False,
                confidence=0.3,
                reasoning="Insufficient evidence.",
                missing_evidence=["Additional evidence"],
            )
        }

    monkeypatch.setattr(wf, "planner_node", planner)
    monkeypatch.setattr(wf, "log_investigator_node", logs)
    monkeypatch.setattr(wf, "metric_investigator_node", logs)
    monkeypatch.setattr(wf, "deployment_investigator_node", logs)
    monkeypatch.setattr(wf, "database_investigator_node", logs)
    monkeypatch.setattr(wf, "configuration_investigator_node", logs)
    monkeypatch.setattr(wf, "correlator_node", correlator)
    monkeypatch.setattr(wf, "evidence_assessment_node", assessment)
    monkeypatch.setattr(wf, "hypothesis_node", hypothesis)
    monkeypatch.setattr(wf, "validator_node", validator)

    budget = LLMBudget()

    result = wf.build_graph().invoke(
        {
            "incident": Incident(
                incident_id="INC-2",
                service="payment-api",
                description="Test iteration-cap incident",
                started_at=datetime(2026, 8, 20, 10),
            ),
            "iteration": 0,
        },
        config={"configurable": {"llm_budget": budget}},
    )

    assert calls["planner"] == wf.MAX_ITERATIONS
    assert calls["validator"] == wf.MAX_ITERATIONS
    assert result["iteration"] == wf.MAX_ITERATIONS
    assert result["status"] == "inconclusive"
    assert "maximum" in result["stop_reason"].lower()
