from dotenv import load_dotenv
import os

load_dotenv()
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from graph.state import IncidentState
from schemas.task import InvestigationTask
from schemas.task import InvestigationPlan

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    temperature=0,
)


PLANNER_PROMPT = """
You are the investigation planner for RootNexus.

Your job is to determine what should be investigated next
for a production incident.

Use:

- the incident
- previous agent findings
- evidence assessment
- current hypotheses
- validation result
- missing evidence
- investigation history

IMPORTANT:

If hypothesis validation failed, inspect the
ValidationResult.missing_evidence field carefully.

Create investigation tasks specifically designed to
collect the missing evidence required to validate or
reject the current hypothesis.

Do NOT blindly repeat investigations that have already
been performed.

Only repeat an investigation when the missing evidence
actually requires additional investigation of that source.

Possible investigation targets:

- logs
- metrics
- deployment
- database
- configuration

Each task must explain WHY that evidence is needed.

Return only an InvestigationPlan.
"""


def planner_node(state: IncidentState):

    incident = state.get("incident")

    findings = state.get(
        "agent_findings",
        [],
    )

    evidence_assessment = state.get(
        "evidence_assessment"
    )

    hypotheses = state.get(
        "hypotheses",
        [],
    )

    validation = state.get(
        "validation"
    )

    history = state.get(
        "investigation_history",
        [],
    )

    prompt = f"""
Incident:

{incident}

Previous findings:

{findings}

Evidence assessment:

{evidence_assessment}

Current hypotheses:

{hypotheses}

Validation result:

{validation}

Missing evidence from validation:

{validation.missing_evidence if validation else []}

Investigation history:

{history}
"""

    structured_llm = llm.with_structured_output(
        InvestigationPlan
    )

    plan = structured_llm.invoke(
        [
            SystemMessage(
                content=PLANNER_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    return {
        "investigation_plan": plan.tasks,
        "iteration": state.get("iteration", 0) + 1,
        "status": "investigating",
    }