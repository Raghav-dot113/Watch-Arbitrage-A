from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from apps.worker.job import JobEnvelope

PipelineHandler = Callable[[JobEnvelope], Coroutine[Any, Any, dict[str, Any]]]


class PipelineProcessor:
    def __init__(self, handlers: dict[str, PipelineHandler]) -> None:
        self._handlers = dict(handlers)

    async def process(self, job: JobEnvelope) -> dict[str, Any]:
        try:
            handler = self._handlers[job.stage]
        except KeyError:
            raise ValueError(f"Unknown pipeline stage: {job.stage}") from None
        return await handler(job)
