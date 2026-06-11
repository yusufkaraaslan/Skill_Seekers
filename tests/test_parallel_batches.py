"""Tests for the shared ThreadPoolExecutor batching helper (Phase 3.1 safe slice).

run_batches_parallel was extracted from three near-identical copies in
ai_enhancer.py (PatternEnhancer/TestExampleEnhancer) and unified_enhancer.py.
"""

import contextvars

import pytest

from skill_seekers.cli.parallel_batches import flatten_batch_results, run_batches_parallel


class TestRunBatchesParallel:
    def test_ordering_preserved(self):
        """Results come back in input order even when batches finish out of order."""
        import time

        batches = [[{"n": i}] for i in range(8)]

        def worker(batch):
            # Earlier batches sleep longer → completion order is reversed
            time.sleep((8 - batch[0]["n"]) * 0.01)
            return [{"n": batch[0]["n"], "enhanced": True}]

        results = run_batches_parallel(batches, worker, max_workers=4)

        assert [r[0]["n"] for r in results] == list(range(8))
        assert all(r[0]["enhanced"] for r in results)

    def test_exception_returns_original_batch(self):
        """A batch whose worker raises is returned unenhanced; others still enhance."""
        batches = [[{"n": 0}], [{"n": 1}], [{"n": 2}]]
        warnings: list[str] = []

        def worker(batch):
            if batch[0]["n"] == 1:
                raise RuntimeError("boom")
            return [{**batch[0], "enhanced": True}]

        results = run_batches_parallel(batches, worker, max_workers=2, warn=warnings.append)

        assert results[0] == [{"n": 0, "enhanced": True}]
        assert results[1] == [{"n": 1}]  # original batch, untouched
        assert results[1] is batches[1]
        assert results[2] == [{"n": 2, "enhanced": True}]
        assert len(warnings) == 1
        assert "Batch 1 failed: boom" in warnings[0]

    def test_contextvars_propagated_to_workers(self):
        """ContextVars set by the caller are visible inside worker threads."""
        var: contextvars.ContextVar[str] = contextvars.ContextVar("test_var", default="unset")
        var.set("from-caller")

        seen: list[str] = []

        def worker(batch):
            seen.append(var.get())
            return batch

        run_batches_parallel([[{"a": 1}], [{"b": 2}], [{"c": 3}]], worker, max_workers=3)

        assert seen == ["from-caller", "from-caller", "from-caller"]

    def test_progress_logging_small_job_logs_every_batch(self):
        """Small jobs (<10 batches) log progress on every completion."""
        logs: list[str] = []
        batches = [[{"n": i}] for i in range(3)]

        run_batches_parallel(batches, lambda b: b, max_workers=2, log=logs.append)

        assert len(logs) == 3
        assert any("3/3 batches completed" in m for m in logs)

    def test_progress_logging_large_job_logs_every_5_and_final(self):
        """Large jobs (>=10 batches) log every 5 completions and at the end."""
        logs: list[str] = []
        batches = [[{"n": i}] for i in range(12)]

        run_batches_parallel(batches, lambda b: b, max_workers=4, log=logs.append)

        # 5/12, 10/12, 12/12
        assert len(logs) == 3
        assert any("12/12 batches completed" in m for m in logs)


class TestFlattenBatchResults:
    def test_flattens_and_skips_empty(self):
        results = [[{"a": 1}, {"b": 2}], [], None, [{"c": 3}]]
        assert flatten_batch_results(results) == [{"a": 1}, {"b": 2}, {"c": 3}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
