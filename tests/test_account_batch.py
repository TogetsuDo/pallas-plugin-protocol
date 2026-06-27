import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "pallas_plugin_protocol"
    / "account_batch.py"
)
_spec = importlib.util.spec_from_file_location("account_batch_under_test", _ROOT)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
AccountBatchCoordinator = _mod.AccountBatchCoordinator
BatchAction = _mod.BatchAction
BatchMode = _mod.BatchMode


@pytest.mark.asyncio
async def test_rolling_restart_runs_sequentially_with_stagger():
    coord = AccountBatchCoordinator()
    order: list[str] = []

    async def stop_fn(aid: str) -> None:
        order.append(f"stop:{aid}")

    async def start_fn(aid: str) -> None:
        order.append(f"start:{aid}")

    async def restart_fn(aid: str) -> None:
        order.append(f"restart:{aid}")

    job_id = await coord.start_job(
        BatchAction.RESTART,
        ["a", "b"],
        stop_fn=stop_fn,
        start_fn=start_fn,
        restart_fn=restart_fn,
        stagger_ms=10,
        mode=BatchMode.ROLLING,
    )
    task = coord._tasks[job_id]
    t0 = asyncio.get_event_loop().time()
    await task
    elapsed = asyncio.get_event_loop().time() - t0
    job = coord.get_job(job_id)
    assert job is not None
    assert job.status == "completed"
    assert job.completed == 2
    assert order == ["stop:a", "stop:b", "start:a", "start:b"]
    assert elapsed >= 0.01


@pytest.mark.asyncio
async def test_parallel_restart_respects_concurrency_cap():
    coord = AccountBatchCoordinator()
    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def stop_fn(aid: str) -> None:
        pass

    async def start_fn(aid: str) -> None:
        pass

    async def restart_fn(aid: str) -> None:
        nonlocal active, peak
        async with lock:
            active += 1
            peak = max(peak, active)
        await asyncio.sleep(0.05)
        async with lock:
            active -= 1

    job_id = await coord.start_job(
        BatchAction.RESTART,
        ["1", "2", "3", "4"],
        stop_fn=stop_fn,
        start_fn=start_fn,
        restart_fn=restart_fn,
        max_concurrency=2,
        mode=BatchMode.PARALLEL,
    )
    await coord._tasks[job_id]
    job = coord.get_job(job_id)
    assert job is not None
    assert job.status == "completed"
    assert job.failed_count == 0
    assert peak <= 2


@pytest.mark.asyncio
async def test_batch_records_failures_without_aborting():
    coord = AccountBatchCoordinator()

    async def stop_fn(aid: str) -> None:
        pass

    async def start_fn(aid: str) -> None:
        if aid == "bad":
            raise ValueError("boom")

    async def restart_fn(aid: str) -> None:
        pass

    job_id = await coord.start_job(
        BatchAction.START,
        ["ok", "bad"],
        stop_fn=stop_fn,
        start_fn=start_fn,
        restart_fn=restart_fn,
        stagger_ms=0,
        mode=BatchMode.ROLLING,
    )
    await coord._tasks[job_id]
    job = coord.get_job(job_id)
    assert job is not None
    assert job.status == "completed"
    assert job.failed_count == 1
    assert any(r.account_id == "bad" and not r.ok for r in job.results)
