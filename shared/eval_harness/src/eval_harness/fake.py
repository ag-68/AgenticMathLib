"""A scripted model client for tests and dry runs. It never calls a provider."""

import copy
from typing import Any

from eval_harness.models import ModelResponse


class FakeClient:
    def __init__(self, script: list[ModelResponse]) -> None:
        self._script = list(script)
        self.seen: list[tuple[list[dict[str, Any]], list[dict[str, Any]] | None]] = []

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> ModelResponse:
        self.seen.append((copy.deepcopy(messages), copy.deepcopy(tools)))
        if not self._script:
            raise RuntimeError("FakeClient script is empty")
        return self._script.pop(0)
