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


DEPLOYMENT_INVESTIGATOR_PROMPT = """
You are the Deployment Investigator for RootNexus.

Analyze deployment evidence and determine whether a recent deployment
could be related to the incident.

Do not invent evidence.

You MUST return an AgentFinding object with ALL four required fields:

1. agent
2. summary
3. evidence
4. confidence

The `summary` field is REQUIRED and must contain a concise explanation
of your finding.

The `evidence` field must contain only evidence present in the input.

The `confidence` field must be a number between 0 and 1.

Return ONLY the structured AgentFinding object.
"""

def deployment_investigator_node(
    state: IncidentState,
) -> dict:

    deployments = state.get("deployments", [])
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

    Deployments:
    {deployments}
    """

    structured_llm = llm.with_structured_output(
        AgentFinding
    )

    finding = structured_llm.invoke(
        [
            SystemMessage(
                content=DEPLOYMENT_INVESTIGATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    finding.agent = "deployment_investigator"

    return {
        "agent_findings": [finding],
        "completed_tasks": [current_task.target],
    }