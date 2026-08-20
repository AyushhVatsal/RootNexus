from dotenv import load_dotenv
import os

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import IncidentState
from schemas.hypothesis import Hypothesis


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    temperature=0,
)


HYPOTHESIS_PROMPT = """
You are the Root Cause Hypothesis Agent for RootNexus.

Your job is to generate a root-cause hypothesis for the
production incident using the available investigation evidence.

Use ONLY the evidence provided.

Do not invent:
- logs
- metrics
- deployments
- database behavior
- configuration changes
- timestamps
- system events

The hypothesis must explain as many of the observed symptoms
as possible.

Identify:

1. The most likely root cause.
2. Evidence supporting the cause.
3. Evidence contradicting the cause.
4. Confidence between 0 and 1.

Do not treat a symptom as the root cause.

For example:
"Payment requests are timing out" is a symptom.

A possible root cause would be:
"Database connection exhaustion is causing request processing
to block until the API timeout."

Return a structured Hypothesis object.
"""


def hypothesis_node(state: IncidentState) -> dict:

    incident = state.get("incident")

    findings = state.get(
        "agent_findings",
        [],
    )

    correlations = state.get(
        "correlations",
        [],
    )

    evidence_assessment = state.get(
        "evidence_assessment"
    )

    prompt = f"""
Incident:

{incident}

Agent findings:

{findings}

Correlations:

{correlations}

Evidence assessment:

{evidence_assessment}
"""

    structured_llm = llm.with_structured_output(
        Hypothesis
    )

    hypothesis = structured_llm.invoke(
        [
            SystemMessage(
                content=HYPOTHESIS_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    return {
        "hypotheses": [hypothesis],
        "status": "hypothesis_generated",
    }