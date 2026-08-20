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

Analyze ONLY the provided deployment information.

Look for:
- recent deployments
- deployment timestamps
- version changes
- configuration changes
- rollbacks
- deployments occurring close to the incident
- relationships between deployment timing and incident timing

Do not assume that a deployment caused the incident merely because
it occurred before the incident.

Identify temporal relationships and provide evidence that can later
be used by the Correlator.

Do not invent deployment information.

Return your result as a structured AgentFinding.
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