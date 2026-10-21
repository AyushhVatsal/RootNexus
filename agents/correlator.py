
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import IncidentState
from schemas.correlation import CorrelationResult
from utils.llm import lazy_llm

llm = lazy_llm("correlator")

CORRELATOR_PROMPT = """
You are the Correlator for RootNexus.

Identify relationships across findings from different evidence sources.

Analyze:
1. Temporal relationships between events.
2. Agreements and contradictions across sources.
3. Relationships between deployments, logs, metrics, and symptoms.
4. Evidence-supported patterns that may help explain the incident.

Do not declare a root cause.
Do not judge whether evidence is sufficient.
Do not invent evidence.
Return only concrete, evidence-supported correlations.
If no meaningful correlations exist, return an empty list.
"""


def correlator_node(state: IncidentState) -> dict:
    incident = state.get("incident")
    findings = state.get("agent_findings", [])

    prompt = f"""
Incident:
{incident}

Investigation findings:
{findings}
"""

    structured_llm = llm.with_structured_output(CorrelationResult)

    result = structured_llm.invoke(
        [
            SystemMessage(content=CORRELATOR_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    iteration = state.get("iteration", 0)
    investigation_plan = state.get("investigation_plan", [])

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
        "result": "Cross-source evidence correlations generated.",
    }

    return {
        "correlations": result.correlations,
        "investigation_history": [history_entry],
        "status": "correlations_generated",
    }
