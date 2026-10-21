
from concurrent.futures import ThreadPoolExecutor

import pytest

from utils.llm_budget import (
    LLMBudget,
    LLMBudgetExceeded,
    bind_budget,
    current_budget,
    reset_budget,
    with_invocation_budget,
)


def test_wrapper_binds_shared_budget():
    budget = LLMBudget(max_calls=2)

    def node(state):
        return current_budget() is budget

    wrapped = with_invocation_budget(node)

    assert wrapped(
        {},
        {"configurable": {"llm_budget": budget}},
    ) is True


def test_wrapper_resets_context_after_node():
    budget = LLMBudget(max_calls=2)

    def node(state):
        raise ValueError("expected test error")

    wrapped = with_invocation_budget(node)

    with pytest.raises(ValueError, match="expected test error"):
        wrapped({}, {"configurable": {"llm_budget": budget}})

    with pytest.raises(RuntimeError, match="No LLM budget is active"):
        current_budget()


def test_budget_rejects_calls_over_limit():
    budget = LLMBudget(max_calls=1)

    budget.reserve(role="planner")

    with pytest.raises(LLMBudgetExceeded):
        budget.reserve(role="investigator")


def test_wrapper_binds_budget_inside_worker_thread():
    budget = LLMBudget(max_calls=2)

    wrapped = with_invocation_budget(
        lambda state: current_budget() is budget
    )

    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(
            wrapped,
            {},
            {"configurable": {"llm_budget": budget}},
        ).result()

    assert result is True
