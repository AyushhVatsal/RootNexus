import logging

from langgraph.types import Send

from graph.state import IncidentState

logger = logging.getLogger("rootnexus.router")

TASK_TO_NODE = {
    "logs": "log_investigator",
    "metrics": "metric_investigator",
    "deployment": "deployment_investigator",
    "database": "database_investigator",
    "configuration": "configuration_investigator",
}


def investigation_router(state: IncidentState) -> list[Send] | str:
    """Fan out the *current* plan to investigators.

    The planner replaces `investigation_plan` every round, so everything in it
    is work for this round. We deliberately do NOT skip targets that finished in
    an earlier round: a follow-up task (e.g. "configuration before the incident")
    often targets a source that was already investigated. Duplicates within one
    plan are collapsed.

    If nothing is routable we go straight to the final report instead of
    returning an empty list, which would leave the graph with nowhere to go.
    """

    tasks = state.get("investigation_plan", [])
    seen: set[str] = set()
    routes: list[Send] = []

    for task in tasks:
        target = task.target.lower().strip()

        if target in seen:
            continue
        node = TASK_TO_NODE.get(target)
        if node is None:
            logger.warning("unknown task target %r skipped", target)
            continue

        seen.add(target)
        routes.append(Send(node, {**state, "current_task": task}))

    if not routes:
        logger.warning("planner produced no routable tasks -> final_report")
        return "final_report"

    return routes