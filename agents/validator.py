from dotenv import load_dotenv
import os

load_dotenv()

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import IncidentState
from schemas.validation import ValidationResult


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    temperature=0,
)


VALIDATOR_PROMPT = """
You are the Hypothesis Validator for RootNexus.

Your job is to determine whether the current root-cause
hypothesis is sufficiently supported by the available evidence.

Evaluate:

- the incident
- the generated hypothesis
- investigator findings
- correlations
- evidence assessment

A hypothesis should only be considered sufficient when the
available evidence provides strong and consistent support for it.

Do NOT assume missing information.

Do NOT invent evidence.

If important evidence is missing, set:

is_sufficient = false

and explicitly list what evidence is required in:

missing_evidence

If the hypothesis is sufficiently supported, set:

is_sufficient = true

and leave missing_evidence empty.

Your confidence must be between 0 and 1.

Return a structured ValidationResult.
"""


def validator_node(state: IncidentState) -> dict:

    incident = state.get("incident")

    hypotheses = state.get(
        "hypotheses",
        [],
    )

    findings = state.get(
        "agent_findings",
        [],
    )

    correlations = state.get(
        "correlations",
        [],
    )

    evidence_assessment = state.get(
        "evidence_assessment"
    )

    prompt = f"""
Incident:

{incident}

Current hypotheses:

{hypotheses}

Investigator findings:

{findings}

Correlations:

{correlations}

Evidence assessment:

{evidence_assessment}
"""

    structured_llm = llm.with_structured_output(
        ValidationResult
    )

    validation = structured_llm.invoke(
        [
            SystemMessage(
                content=VALIDATOR_PROMPT
            ),
            HumanMessage(
                content=prompt
            ),
        ]
    )

    return {
        "validation": validation,
        "status": "validated",
    }