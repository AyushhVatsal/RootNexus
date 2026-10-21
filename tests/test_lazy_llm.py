
from unittest.mock import MagicMock, patch

import pytest

from utils.llm import LazyLLM
from utils.llm_budget import LLMBudget, bind_budget, reset_budget


def test_invoke_counts_one_call():
    budget = LLMBudget(max_calls=2)
    token = bind_budget(budget)

    try:
        llm = LazyLLM("test")
        fake_model = MagicMock()
        fake_model.invoke.return_value = "ok"
        llm._model = fake_model

        result = llm.invoke("test input")

        assert result == "ok"
        assert budget.calls == 1
        fake_model.invoke.assert_called_once_with("test input")
    finally:
        reset_budget(token)


def test_structured_output_counts_one_call():
    budget = LLMBudget(max_calls=2)
    token = bind_budget(budget)

    try:
        llm = LazyLLM("test")
        fake_model = MagicMock()
        fake_runnable = MagicMock()
        fake_runnable.invoke.return_value = {"ok": True}
        fake_model.with_structured_output.return_value = fake_runnable
        llm._model = fake_model

        runnable = llm.with_structured_output(dict)
        result = runnable.invoke({"input": "test"})

        assert result == {"ok": True}
        assert budget.calls == 1
        fake_runnable.invoke.assert_called_once()
    finally:
        reset_budget(token)


def test_rejected_invoke_does_not_reach_model():
    budget = LLMBudget(max_calls=1)
    token = bind_budget(budget)

    try:
        llm = LazyLLM("test")
        fake_model = MagicMock()
        llm._model = fake_model

        budget.reserve(role="first")

        from utils.llm_budget import LLMBudgetExceeded

        with pytest.raises(LLMBudgetExceeded):
            llm.invoke("second call")

        fake_model.invoke.assert_not_called()
        assert budget.calls == 1
    finally:
        reset_budget(token)
