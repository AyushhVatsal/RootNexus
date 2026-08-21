from langgraph.types import Send
from graph.state import IncidentState


TASK_TO_NODE = {
    "logs": "log_investigator",
    "metrics": "metric_investigator",
    "deployment": "deployment_investigator",
    "database": "database_investigator",
    "configuration": "configuration_investigator",
}


def investigation_router(state: IncidentState) -> list[Send]:

    tasks = state.get("investigation_plan", [])
    completed = set(state.get("completed_tasks", []))

    routes = []

    for task in tasks:

        target = task.target.lower().strip()

        # Skip already completed tasks
        if target in completed:
            continue

        node = TASK_TO_NODE.get(target)

        if node is None:
            continue

        routes.append(
            Send(
                node,
                {
                    **state,
                    "current_task": task,
                },
            )
        )

    return routes