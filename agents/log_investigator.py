from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import IncidentState
from schemas.finding import AgentFinding
from utils.llm import lazy_llm


llm = lazy_llm("log_investigator")



LOG_INVESTIGATOR_PROMPT = """
You are the Log Investigator for RootNexus.

Analyze ONLY the provided application logs.

Do not invent evidence.

Return ONLY an AgentFinding matching the provided schema.

Required fields:
- agent
- summary
- evidence
- confidence

Rules:
1. agent must be exactly "log_investigator".
2. summary must be a plain string.
3. evidence must contain only exact log entries copied from the input.
4. confidence must be a JSON number between 0 and 1.
5. Do not use markdown.
6. Do not use special formatting.
7. Do not write numbers as words.
8. Do not include additional fields.
"""


def log_investigator_node(
    state: IncidentState,
) -> dict:

    logs = state.get("logs", "")
    incident = state.get("incident")
    current_task = state.get("current_task")

    if current_task is None:
        raise ValueError(
            "No current investigation task assigned"
        )

    prompt = f"""
    Incident:

    {incident}

    Investigation task:

    {current_task}

    Logs:

    {logs}

    """

    structured_llm = llm.with_structured_output(
        AgentFinding
    )

    finding = structured_llm.invoke(
        [
            SystemMessage(
                content=LOG_INVESTIGATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    finding.agent = "log_investigator"

    return {
        "agent_findings": [finding],
        "completed_tasks": [current_task.target],
    }