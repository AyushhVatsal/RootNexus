
from unittest.mock import MagicMock

from utils.llm import LazyLLM
from utils.llm_budget import LLMBudget, bind_budget, reset_budget


def test_structured_output_retries_and_counts_attempts():
    budget = LLMBudget(max_calls=3)
    token = bind_budget(budget)

    try:
        llm = LazyLLM("test")
        fake_model = MagicMock()
        fake_runnable = MagicMock()

        fake_runnable.invoke.side_effect = [
            ValueError("temporary failure"),
            ValueError("temporary failure"),
            {"ok": True},
        ]
        fake_model.with_structured_output.return_value = fake_runnable
        llm._model = fake_model

        result = llm.with_structured_output(dict).invoke(
            {"input": "test"}
        )

        assert result == {"ok": True}
        assert budget.calls == 3
        assert fake_runnable.invoke.call_count == 3
    finally:
        reset_budget(token)
