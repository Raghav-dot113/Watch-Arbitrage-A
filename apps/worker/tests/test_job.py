from __future__ import annotations

import pytest
from apps.worker.job import JobEnvelope, make_idempotency_key
from apps.worker.pipeline import PipelineProcessor


def test_job_envelope_rejects_bad_trace_id() -> None:
    with pytest.raises(ValueError):
        JobEnvelope(
            trace_id="bad",
            stage="fetch",
            payload={"source_id": "src_1"},
            idempotency_key="idem_1",
        )


def test_job_retry_is_bounded() -> None:
    job = JobEnvelope(
        trace_id="trc_test",
        stage="fetch",
        payload={"source_id": "src_1"},
        idempotency_key="idem_1",
        max_attempts=1,
    )
    with pytest.raises(RuntimeError):
        job.next_attempt()


def test_idempotency_key_is_stable() -> None:
    payload = {"source_id": "src_1", "external_id": "watch_1"}
    first = make_idempotency_key("fetch", payload, "v1")
    second = make_idempotency_key("fetch", dict(reversed(payload.items())), "v1")
    assert first == second


@pytest.mark.asyncio
async def test_pipeline_processor_unknown_stage_is_explicit() -> None:
    processor = PipelineProcessor({})
    job = JobEnvelope(
        trace_id="trc_test",
        stage="unknown",
        payload={},
        idempotency_key="idem_1",
    )
    with pytest.raises(ValueError, match="Unknown pipeline stage"):
        await processor.process(job)
