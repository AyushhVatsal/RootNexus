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


METRICS_INVESTIGATOR_PROMPT = """
You are the Metrics Investigator for RootNexus.

Analyze ONLY the provided incident metrics.

Look for:
- error-rate changes
- latency changes
- traffic changes
- resource utilization
- unusual spikes or drops
- changes that correlate with the incident time
- signs of degradation or recovery

Compare the metric behavior with the incident timeline.

Do not invent metrics or values that are not provided.

Return your result as a structured AgentFinding.
"""


def metric_investigator_node(
    state: IncidentState,
) -> dict:

    metrics = state.get("metrics", {})
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

    Metrics:
    {metrics}
    """

    structured_llm = llm.with_structured_output(
        AgentFinding,
        method="json_schema",
    )

    finding = structured_llm.invoke(
        [
            SystemMessage(
                content=METRICS_INVESTIGATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    finding.agent = "metric_investigator"

    return {
        "agent_findings": [finding],
        "completed_tasks": [current_task.target],
    }