from dotenv import load_dotenv
import os

load_dotenv()
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import IncidentState
from schemas.finding import AgentFinding


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    temperature=0,
)


LOG_INVESTIGATOR_PROMPT = """
You are the Log Investigator for RootNexus.

Analyze ONLY the provided application logs.

Look for:
- errors
- exceptions
- recurring failures
- timestamps
- affected components
- unusual patterns
- events that may explain the incident

Do not invent information that is not present in the logs.

Return your result as a structured AgentFinding.
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