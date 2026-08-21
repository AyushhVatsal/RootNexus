from datetime import datetime
from schemas.evidence import EvidenceAssessment
from graph.workflow import build_graph
from schemas.incident import Incident
from schemas.validation import ValidationResult
from schemas.hypothesis import Hypothesis

graph = build_graph()


incident = Incident(
    incident_id="INC-001",
    service="payment-api",
    description="Payment API latency increased significantly and requests are timing out.",
    started_at=datetime.fromisoformat(
        "2026-08-20T10:00:00"
    ),
)


initial_state = {
    "incident": incident,

    "logs": """
2026-08-20T10:01:12 ERROR database connection timeout
2026-08-20T10:01:18 ERROR database connection timeout
2026-08-20T10:01:22 ERROR database connection pool exhausted
2026-08-20T10:01:25 ERROR payment request timeout
""",

    "metrics": {
        "latency_ms": 4200,
        "error_rate": 0.18,
        "request_rate": 850,
        "db_connection_pool_usage": 0.98,
    },

    "deployments": [],

    "other_evidence": {
        "database": {
            "connection_pool": 98,
            "query_latency_ms": 1800,
        }
    },

    # Existing evidence assessment says evidence is sufficient
    "evidence_assessment": EvidenceAssessment(
        sufficient=True,
        reasoning="Evidence is sufficient for hypothesis generation.",
        coverage=0.8,
        consistency=0.9,
        temporal_correlation=0.9,
        causal_support=0.8,
        missing_evidence=[],
    ),

    # Existing hypothesis
    "hypotheses": [
        Hypothesis(
            cause="Database connection pool exhaustion caused payment-API latency spikes and timeouts.",
            supporting_evidence=[
                "database connection timeout",
                "database connection pool exhausted",
                "latency_ms=4200",
                "db_connection_pool_usage=0.98",
            ],
            contradicting_evidence=[],
            confidence=0.85,
        )
    ],

    # THIS is the branch we want to test
    "validation": ValidationResult(
        is_sufficient=False,
        confidence=0.4,
        reasoning=(
            "The hypothesis is plausible, but direct evidence "
            "confirming the database connection pool configuration "
            "before the incident is missing."
        ),
        missing_evidence=[
            "database connection pool configuration before the incident"
        ],
    ),

    "agent_findings": [],
    "correlations": [],
    "investigation_history": [],

    "iteration": 1,
    "status": "validated",
    "completed_tasks": [],
}


result = graph.invoke(initial_state)

import json

print("\n=== FINAL STATE ===")
print(json.dumps(result, indent=2, default=str))