from datetime import datetime

from graph.workflow import build_graph
from schemas.incident import Incident


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
2026-08-20T10:01:14 ERROR payment request timeout
2026-08-20T10:01:18 ERROR database connection timeout
""",

    "metrics": {
        "latency_ms": 4200,
        "error_rate": 0.18,
    },

    "deployments": [],

    "other_evidence": {},

    "agent_findings": [],
    "correlations": [],
    "hypotheses": [],
    "investigation_history": [],

    "iteration": 0,
    "status": "starting",
}


result = graph.invoke(initial_state)


print("\n=== FINAL STATE ===")
print(result)