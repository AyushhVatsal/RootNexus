from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import IncidentState
from schemas.finding import AgentFinding
from utils.llm import lazy_llm

llm = lazy_llm("configuration_investigator")


CONFIGURATION_INVESTIGATOR_PROMPT = """
You are the Configuration Investigator for RootNexus.

Analyze the provided configuration-related evidence.

Look for:
- configuration changes
- environment changes
- feature flags
- threshold changes
- connection settings
- configuration changes occurring before the incident

Do not assume that a configuration change caused the incident.

Do not invent evidence.

Return a structured AgentFinding.
"""


def configuration_investigator_node(
    state: IncidentState,
) -> dict:

    incident = state.get("incident")

    current_task = state.get("current_task")

    if current_task is None:
        raise ValueError(
            "No current investigation task assigned"
        )

    other_evidence = state.get(
        "other_evidence",
        {}
    )

    prompt = f"""
    Incident:
    {incident}

    Investigation task:
    {current_task}

    Configuration-related evidence:
    {other_evidence}
    """
    structured_llm = llm.with_structured_output(
        AgentFinding
    )

    finding = structured_llm.invoke(
        [
            SystemMessage(
                content=CONFIGURATION_INVESTIGATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    finding.agent = "configuration_investigator"

    return {
        "agent_findings": [finding],
        "completed_tasks": [current_task.target],
    }