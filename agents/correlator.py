from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()

from graph.state import IncidentState
from schemas.evidence import EvidenceAssessment


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


CORRELATOR_PROMPT = """
You are the Correlator for RootNexus.

You receive findings produced by multiple incident investigation
agents.

Your job is to correlate the findings and determine whether the
available evidence is sufficient to begin root-cause hypothesis
generation.

Analyze:

1. Coverage
   Do the findings cover the important aspects of the incident?

2. Consistency
   Do the different evidence sources support or contradict each
   other?

3. Temporal correlation
   Did important changes occur around the incident timeline?

4. Causal support
   Is there evidence that could plausibly explain the incident?

Do NOT declare a root cause.

Do NOT invent evidence.

The purpose of this step is only to determine whether there is
enough evidence to proceed to hypothesis generation.

Return a structured EvidenceAssessment.
"""


def correlator_node(
    state: IncidentState,
) -> dict:

    incident = state.get("incident")
    findings = state.get("agent_findings", [])

    prompt = f"""
Incident:
{incident}

Investigation findings:
{findings}
"""

    structured_llm = llm.with_structured_output(
        EvidenceAssessment
    )

    assessment = structured_llm.invoke(
        [
            SystemMessage(
                content=CORRELATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    correlations = [
        assessment.reasoning
    ]

    history = state.get(
        "investigation_history",
        []
    )

    iteration = state.get(
        "iteration",
        0
    )

    investigation_plan = state.get(
        "investigation_plan",
        []
    )

    history_entry = {
        "iteration": iteration,
        "tasks": [
            {
                "target": task.target,
                "reason": task.reason,
                "priority": task.priority,
            }
            for task in investigation_plan
        ],
        "result": (
            "Investigation completed and "
            "findings correlated."
        ),
    }

    return {
        "evidence_assessment": assessment,

        "correlations": correlations,

        "investigation_history": [
            history_entry
        ],

        "status": (
            "evidence_sufficient"
            if assessment.sufficient
            else "evidence_insufficient"
        ),
    }