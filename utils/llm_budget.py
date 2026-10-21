"""Per-investigation LLM call budget for RootNexus."""

from contextvars import ContextVar
from threading import Lock


MAX_LLM_CALLS = 15


class LLMBudgetExceeded(RuntimeError):
    """Raised when an investigation exhausts its LLM call budget."""


class LLMBudget:
    """Thread-safe counter for LLM attempts within one investigation."""

    def __init__(self, max_calls: int = MAX_LLM_CALLS) -> None:
        if max_calls < 1:
            raise ValueError("max_calls must be at least 1")

        self.max_calls = max_calls
        self._calls = 0
        self._lock = Lock()

    @property
    def calls(self) -> int:
        with self._lock:
            return self._calls

    def reserve(self, *, role: str = "unknown") -> int:
        """Reserve one call before invoking the provider."""
        with self._lock:
            if self._calls >= self.max_calls:
                raise LLMBudgetExceeded(
                    f"LLM call budget exceeded ({self.max_calls}); "
                    f"role={role!r}"
                )

            self._calls += 1
            return self._calls


_current_budget: ContextVar[LLMBudget | None] = ContextVar(
    "rootnexus_llm_budget",
    default=None,
)


def current_budget() -> LLMBudget:
    """Return the budget bound to the current execution context."""
    budget = _current_budget.get()

    if budget is None:
        raise RuntimeError(
            "No LLM budget is active. Bind an LLMBudget "
            "at the start of the investigation."
        )

    return budget


def bind_budget(budget: LLMBudget):
    """Bind a budget and return a token for restoring the previous context."""
    return _current_budget.set(budget)


def reset_budget(token) -> None:
    """Restore the previous budget context."""
    _current_budget.reset(token)

def with_invocation_budget(node):
    """Bind the shared investigation budget within a graph node."""

    def wrapped(state, config=None):
        configurable = (config or {}).get("configurable", {})
        budget = configurable.get("llm_budget")

        if budget is None:
            raise RuntimeError(
                "Missing llm_budget in graph invocation config."
            )

        token = bind_budget(budget)
        try:
            return node(state)
        finally:
            reset_budget(token)

    return wrapped

__all__ = [
    "MAX_LLM_CALLS",
    "LLMBudget",
    "LLMBudgetExceeded",
    "bind_budget",
    "check_llm_budget",
    "current_budget",
    "reset_budget",
    "with_invocation_budget",
]


def check_llm_budget(state: dict) -> int:
    """Check a graph state's call count without mutating it."""
    calls = state.get("llm_calls", 0)

    if calls >= MAX_LLM_CALLS:
        raise LLMBudgetExceeded(
            f"LLM call budget exceeded: {MAX_LLM_CALLS}"
        )

    return calls + 1
