
"""Shared, lazily initialized LLM factory for RootNexus."""

import os
from threading import Lock
from typing import Any

from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda

from utils.llm_budget import LLMBudgetExceeded, current_budget

load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-120b"
STRUCTURED_OUTPUT_ATTEMPTS = 3

def resolve_model(role: str, model: str | None = None) -> str:
    """Resolve an explicit model, role-specific model, or fallback."""
    if model and model.strip():
        return model.strip()

    normalized_role = role.strip().upper()
    if not normalized_role:
        raise ValueError("LLM role cannot be empty")

    candidates = (
        os.getenv(f"ROOTNEXUS_MODEL_{normalized_role}"),
        os.getenv("GROQ_MODEL"),
        DEFAULT_MODEL,
    )

    for candidate in candidates:
        if candidate and candidate.strip():
            return candidate.strip()

    raise ValueError("No valid LLM model configured")


class LazyLLM:
    """Lazy LLM wrapper with centralized budget enforcement."""

    def __init__(
        self,
        role: str,
        *,
        model: str | None = None,
        budget: Any = None,
        **kwargs: Any,
    ) -> None:
        normalized_role = role.strip().lower()
        if not normalized_role:
            raise ValueError("LLM role cannot be empty")

        self.role = normalized_role
        self.model = model
        self.budget = budget
        self.kwargs = kwargs
        self._model = None
        self._lock = Lock()

    def _budget(self) -> Any:
        """Get the explicitly supplied or context-bound budget."""
        return self.budget if self.budget is not None else current_budget()

    def _get(self) -> Any:
        """Construct the provider client on first use."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from langchain_groq import ChatGroq

                    model_kwargs = dict(self.kwargs)
                    model_kwargs.setdefault("temperature", 0)

                    self._model = ChatGroq(
                        model=resolve_model(self.role, self.model),
                        **model_kwargs,
                    )

        return self._model

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Reserve budget before making a model call."""
        self._budget().reserve(role=self.role)
        return self._get().invoke(*args, **kwargs)
    def with_structured_output(
        self,
        schema: Any,
        **kwargs: Any,
    ) -> Any:
        """Return structured output with retries and budget enforcement."""
        runnable = self._get().with_structured_output(
            schema,
            **kwargs,
        )

        def invoke_structured(
            input: Any,
            config: Any = None,
            **invoke_kwargs: Any,
        ) -> Any:
            # Count each actual attempt, including retries.
            self._budget().reserve(role=self.role)
            return runnable.invoke(
                input,
                config=config,
                **invoke_kwargs,
            )

        return RunnableLambda(invoke_structured).with_retry(
            stop_after_attempt=3,
            wait_exponential_jitter=True,
        )

def lazy_llm(
    role: str,
    *,
    model: str | None = None,
    budget: Any = None,
    **kwargs: Any,
) -> LazyLLM:
    """Create a lazy LLM wrapper for an agent role."""
    return LazyLLM(
        role,
        model=model,
        budget=budget,
        **kwargs,
    )


__all__ = [
    "DEFAULT_MODEL",
    "LLMBudgetExceeded",
    "LazyLLM",
    "lazy_llm",
    "resolve_model",
]
