from dotenv import load_dotenv
import os

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import IncidentState
from schemas.evidence import EvidenceAssessment


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


EVIDENCE_ASSESSMENT_PROMPT = """
You are the Evidence Assessment Agent for RootNexus.

Your job is to determine whether the investigation has enough
relevant evidence to generate a meaningful root-cause hypothesis.

Evaluate the available:

- investigator findings
- correlations
- logs
- metrics
- deployments
- configuration evidence
- database evidence

Assess:

1. Evidence coverage
2. Evidence consistency
3. Temporal correlation
4. Causal support

Set sufficient=True only when there is enough relevant,
consistent evidence to proceed to hypothesis generation.

If important evidence is missing, set sufficient=False.

Do not invent evidence.

If evidence is insufficient, list the missing evidence
that should be investigated next.

Return a structured EvidenceAssessment object.
"""


def evidence_assessment_node(
    state: IncidentState,
) -> dict:

    incident = state.get("incident")

    findings = state.get(
        "agent_findings",
        [],
    )

    correlations = state.get(
        "correlations",
        [],
    )

    logs = state.get(
        "logs",
        "",
    )

    metrics = state.get(
        "metrics",
        {},
    )

    deployments = state.get(
        "deployments",
        [],
    )

    other_evidence = state.get(
        "other_evidence",
        {},
    )

    prompt = f"""
Incident:

{incident}

Investigator findings:

{findings}

Correlations:

{correlations}

Logs:

{logs}

Metrics:

{metrics}

Deployments:

{deployments}

Other evidence:

{other_evidence}
"""

    structured_llm = llm.with_structured_output(
        EvidenceAssessment
    )

    assessment = structured_llm.invoke(
        [
            SystemMessage(
                content=EVIDENCE_ASSESSMENT_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    return {
        "evidence_assessment": assessment,
        "status": "evidence_assessed",
    }