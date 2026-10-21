from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import IncidentState
from schemas.validation import ValidationResult
from utils.llm import lazy_llm

llm = lazy_llm(
    "validator",
    model="openai/gpt-oss-120b",
)


VALIDATOR_PROMPT = """
You are the Hypothesis Validator for RootNexus.

Determine whether the current root-cause hypothesis is sufficiently
supported by the available evidence.

Rules:

1. Do NOT invent evidence.
2. Do NOT assume missing information.
3. Set is_sufficient=true only when the evidence strongly supports
   the hypothesis.
4. If important evidence is missing, set is_sufficient=false.
5. If is_sufficient=false, missing_evidence MUST contain the specific
   missing evidence required.
6. If is_sufficient=true, missing_evidence MUST be an empty list.
7. confidence MUST be a JSON NUMBER between 0 and 1.
8. Use decimal notation for confidence, for example 0.9 or 0.95.
9. NEVER write numbers as words.
10. Return ONLY a valid ValidationResult matching the provided schema.

The output must contain:

{
    "is_sufficient": true,
    "confidence": 0.95,
    "reasoning": "...",
    "missing_evidence": []
}
"""


def validator_node(state: IncidentState) -> dict:

    incident = state.get("incident")
    hypotheses = state.get("hypotheses", [])
    correlations = state.get("correlations", [])
    evidence_assessment = state.get("evidence_assessment")

    latest_hypothesis = (
        hypotheses[-1]
        if hypotheses
        else None
    )

    prompt = f"""
Incident:
{incident.description if incident else "Unknown"}

Current hypothesis:
{latest_hypothesis}

Evidence assessment:
{evidence_assessment}

Key correlations:
{correlations[-3:]}
"""

    structured_llm = llm.with_structured_output(
        ValidationResult,
        method="function_calling",
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