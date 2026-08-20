from graph.state import IncidentState


def investigation_barrier(
    state: IncidentState,
) -> dict:

    selected_tasks = state.get(
        "selected_tasks",
        []
    )

    completed_tasks = state.get(
        "completed_tasks",
        []
    )

    selected_targets = {
        task.target
        for task in selected_tasks
    }

    completed_targets = set(
        completed_tasks
    )

    if selected_targets.issubset(completed_targets):
        return {
            "next_action": "correlate",
        }

    return {
        "next_action": "wait",
    }