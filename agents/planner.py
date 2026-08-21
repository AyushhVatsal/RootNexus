from dotenv import load_dotenv
import os

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import IncidentState
from schemas.task import InvestigationPlan


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


PLANNER_PROMPT = """
You are the investigation planner for RootNexus.

Your job is to determine what should be investigated next
for a production incident.

Use:
- the incident
- previous agent findings
- evidence assessment
- current hypothesis
- validation result
- missing evidence
- investigation history

IMPORTANT:

If hypothesis validation failed, inspect the
ValidationResult.missing_evidence field carefully.

Create investigation tasks specifically designed to
collect the missing evidence required to validate or
reject the current hypothesis.

Do NOT blindly repeat investigations that have already
been performed.

Only repeat an investigation when the missing evidence
actually requires additional investigation of that source.

The target field MUST be exactly one of:
logs
metrics
deployment
database
configuration

Each task must explain WHY that evidence is needed.

Return an InvestigationPlan.

The InvestigationPlan MUST contain a top-level "tasks" field.

Each task MUST contain:
- target
- reason
- priority

Do NOT return "description", "properties", or any other
wrapper around "tasks".
"""

def planner_node(state: IncidentState):

    incident = state.get("incident")

    findings = state.get(
        "agent_findings",
        [],
    )

    evidence_assessment = state.get(
        "evidence_assessment"
    )

    hypotheses = state.get(
        "hypotheses",
        [],
    )

    validation = state.get(
        "validation"
    )

    history = state.get(
        "investigation_history",
        [],
    )

    # -----------------------------------------
    # Compact incident
    # -----------------------------------------

    incident_context = None

    if incident:

        incident_context = {
            "incident_id": incident.incident_id,
            "service": incident.service,
            "description": incident.description,
            "started_at": incident.started_at.isoformat(),
        }

    # -----------------------------------------
    # Compact findings
    # -----------------------------------------

    findings_context = [
        {
            "agent": finding.agent,
            "summary": finding.summary,
            "confidence": finding.confidence,
        }
        for finding in findings
    ]

    # -----------------------------------------
    # Compact evidence assessment
    # -----------------------------------------

    evidence_context = None

    if evidence_assessment:

        evidence_context = {
            "sufficient": evidence_assessment.sufficient,
            "reasoning": evidence_assessment.reasoning,
            "missing_evidence": (
                evidence_assessment.missing_evidence
            ),
        }

    # -----------------------------------------
    # Compact current hypothesis
    # -----------------------------------------

    hypothesis_context = None

    if hypotheses:

        hypothesis = hypotheses[-1]

        hypothesis_context = {
            "cause": hypothesis.cause,
            "confidence": hypothesis.confidence,
            "supporting_evidence": (
                hypothesis.supporting_evidence
            ),
            "contradicting_evidence": (
                hypothesis.contradicting_evidence
            ),
        }

    # -----------------------------------------
    # Compact validation
    # -----------------------------------------

    validation_context = None

    if validation:

        validation_context = {
            "is_sufficient": validation.is_sufficient,
            "confidence": validation.confidence,
            "reasoning": validation.reasoning,
            "missing_evidence": (
                validation.missing_evidence
            ),
        }

    # -----------------------------------------
    # Compact investigation history
    # -----------------------------------------

    history_context = [
        {
            "iteration": item.get("iteration"),
            "tasks": item.get("tasks", []),
            "result": item.get("result"),
        }
        for item in history
    ]

    # -----------------------------------------
    # Planner input
    # -----------------------------------------

    prompt = f"""
Incident:
{incident_context}

Previous findings:
{findings_context}

Evidence assessment:
{evidence_context}

Current hypothesis:
{hypothesis_context}

Validation result:
{validation_context}

Investigation history:
{history_context}
"""

    # -----------------------------------------
    # Structured output
    # -----------------------------------------

    structured_llm = llm.with_structured_output(
        InvestigationPlan,
        method="json_schema",
    )

    plan = structured_llm.invoke(
        [
            SystemMessage(
                content=PLANNER_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    return {
        "investigation_plan": plan.tasks,
        "iteration": state.get("iteration", 0) + 1,
        "status": "investigating",
    }