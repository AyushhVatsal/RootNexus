from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import IncidentState
from schemas.hypothesis import Hypothesis
from utils.llm import lazy_llm

llm = lazy_llm(
    "hypothesis",
    model="openai/gpt-oss-120b",
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
    logs = state.get("logs", "")
    metrics = state.get("metrics", {})
    deployments = state.get("deployments", [])
    other_evidence = state.get("other_evidence", {})

    previous_hypotheses = state.get("hypotheses", [])
    validation = state.get("validation")
    investigation_history = state.get("investigation_history", [])

    prompt = f"""
Incident:
{incident}

Raw logs:
{logs}

Raw metrics:
{metrics}

Deployments:
{deployments}

Other evidence:
{other_evidence}

Previous hypotheses:
{previous_hypotheses}

Latest validator feedback:
{validation}

Investigation history:
{investigation_history}

Revise or improve the hypothesis using the available evidence and feedback.
Do not simply repeat a rejected hypothesis.
Treat high latency and resource exhaustion as symptoms unless evidence
supports them as the underlying root cause.
Do not invent facts or claim that a hypothesis is validated without evidence.
"""

    structured_llm = llm.with_structured_output(Hypothesis)

    hypothesis = structured_llm.invoke(
        [
            SystemMessage(content=HYPOTHESIS_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "hypotheses": [hypothesis],
        "status": "hypothesis_generated",
    }