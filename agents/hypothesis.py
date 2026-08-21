from dotenv import load_dotenv
import os

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import IncidentState
from schemas.hypothesis import Hypothesis


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


HYPOTHESIS_PROMPT = """
You are the Root Cause Hypothesis Agent for RootNexus.

Return ONLY a JSON object with EXACTLY these top-level fields:

{
    "cause": "string",
    "supporting_evidence": ["string"],
    "contradicting_evidence": ["string"],
    "confidence": 0.0
}

Do NOT put these fields inside another object such as
"properties".

Do NOT return "description" or "properties".

Use ONLY the evidence provided.

Do not invent logs, metrics, deployments, database behavior,
configuration changes, timestamps, or system events.

The hypothesis must explain as many observed symptoms as possible.

Do not treat a symptom as the root cause.

Incident:
...
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
        Hypothesis,
        method="json_mode",
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