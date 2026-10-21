
import pytest

from utils.llm_budget import LLMBudget, LLMBudgetExceeded


def test_budget_allows_calls_up_to_limit():
    budget = LLMBudget(max_calls=15)

    for _ in range(15):
        budget.reserve(role="test")

    assert budget.calls == 15


def test_budget_rejects_call_over_limit():
    budget = LLMBudget(max_calls=15)

    for _ in range(15):
        budget.reserve(role="test")

    with pytest.raises(LLMBudgetExceeded):
        budget.reserve(role="test")

    assert budget.calls == 15

def test_budget_allows_exactly_max_calls():
    budget = LLMBudget(max_calls=15)

    for _ in range(15):
        budget.reserve(role="test")

    assert budget.calls == 15


def test_budget_rejects_sixteenth_call():
    budget = LLMBudget(max_calls=15)

    for _ in range(15):
        budget.reserve(role="test")

    with pytest.raises(LLMBudgetExceeded):
        budget.reserve(role="test")

    assert budget.calls == 15


def test_each_investigation_has_an_independent_budget():
    first = LLMBudget(max_calls=2)
    second = LLMBudget(max_calls=2)

    first.reserve(role="planner")
    first.reserve(role="validator")
    second.reserve(role="planner")

    assert first.calls == 2
    assert second.calls == 1