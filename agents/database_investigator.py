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


DATABASE_INVESTIGATOR_PROMPT = """
You are the Database Investigator for RootNexus.

Analyze the provided incident information and database-related
evidence.

Look for:
- database errors
- connection failures
- query failures
- connection pool exhaustion
- database latency
- database availability problems
- events occurring around the incident timeline

Do not invent evidence.

Return a structured AgentFinding.
"""


def database_investigator_node(
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

    Database-related evidence:
    {other_evidence}
    """

    structured_llm = llm.with_structured_output(
        AgentFinding
    )

    finding = structured_llm.invoke(
        [
            SystemMessage(
                content=DATABASE_INVESTIGATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    finding.agent = "database_investigator"

    return {
        "agent_findings": [finding],
        "completed_tasks": [current_task.target],
    }