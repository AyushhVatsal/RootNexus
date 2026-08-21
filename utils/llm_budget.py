MAX_LLM_CALLS = 15


def check_llm_budget(state):
    calls = state.get("llm_calls", 0)

    if calls >= MAX_LLM_CALLS:
        raise RuntimeError(
            f"LLM call budget exceeded: {MAX_LLM_CALLS}"
        )

    return calls + 1